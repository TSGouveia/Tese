# AAS Control Logic Rules & Sequences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate a visual programming/logic control step inside the PyQt6 Conveyor Wizard and implement a C# rule execution engine in Unity to run start sequences and triggered conditional logic using a driver abstraction.

**Architecture:** 
1. Expand the PyQt6 Conveyor Wizard to add a 3-panel step to define Arduino-like Start and triggered Sequences (JSON rules).
2. Save these rules under a new `ControlLogic` submodel inside the AAS package.
3. Build a Unity execution engine (`AASRuleEngine.cs`) that fetches, parses, and runs the sequences sequentially in Coroutines using a driver abstraction (`IAASDriver`) to enable low-latency local execution with BaSyx synchronization.

**Tech Stack:** PyQt6, Python basyx-python-sdk, Unity C#, Newtonsoft.Json.

---

### Task 1: Extend PyQt6 Wizard UI with Control Logic Step

**Files:**
- Modify: `AAS Client/conveyor_wizard.py`

- [ ] **Step 1.1: Create UI elements for the Control Logic Page**
  Add a page class or widgets inside `ConveyorWizard.setup_steps` to hold:
  - List of sequences (Left Panel: QListWidget, Add Sequence, Delete Sequence).
  - Trigger conditions (Middle Panel: QGroupBox, AND/OR selector, scroll area of trigger conditions: sensor dropdown + value checkbox/dropdown).
  - Sequence steps list (Right Panel: QListWidget, Add Set Actuator, Add Wait Until, Add Wait Time, Move Up, Move Down, Delete Step).
  - Bottom edit pane: dynamic layout displaying parameters of the currently selected step.

- [ ] **Step 1.2: Populate Sensor and Actuator Dropdowns**
  Connect the logic editor dropdowns to populate dynamically from the wizard's sensor lists (`self.sensor_widgets`) and actuator lists (`self.actuator_widgets`).

- [ ] **Step 1.3: Support JSON Serialization & Preview**
  Implement logic to serialize the PyQt UI state into the target JSON structure and update the preview step JSON content.

- [ ] **Step 1.4: Update Step Indexes and Wizard Navigation**
  Ensure the logic page is Step 5 of 6, shifting the Preview/Deploy page to Step 6. Adjust `self.btn_next` label and transition states in `update_step_label()`.

- [ ] **Step 1.5: Commit changes**
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: add Control Logic UI step in Conveyor Wizard"
  ```

---

### Task 2: Include `ControlLogic` Submodel in AAS Generation and Clone Parsing

**Files:**
- Modify: `AAS Client/conveyor_wizard.py`

- [ ] **Step 2.1: Add Submodel Creation to `deploy_to_aas`**
  Modify the `deploy_to_aas` function to instantiate the `ControlLogic` submodel, create the `Rules` Property, write the serialized JSON string into it, and add it to the `AssetAdministrationShell` package.

- [ ] **Step 2.2: Add Submodel Parsing to Clone / Load Logic**
  Modify the cloned AAS loading function (`load_cloned_aas` or equivalent) to parse the `ControlLogic` submodel if it exists, deserializing the JSON rules back into the wizard's PyQt logic rules UI.

- [ ] **Step 2.3: Test PyQt6 code execution**
  Run the client wizard script to ensure no syntax errors and verify that the steps render properly.
  Run: `python "AAS Client/conveyor_wizard.py"`

- [ ] **Step 2.4: Commit changes**
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: integrate ControlLogic submodel in AAS generation & clone parsing"
  ```

---

### Task 3: Implement Unity Driver Abstraction (`IAASDriver`)

**Files:**
- Create: `DT Unity/Assets/Scripts/AAS/IAASDriver.cs`

- [ ] **Step 3.1: Define `IAASDriver` interface and `AASHttpDriver` class**
  Create the interface and its HTTP implementation that interacts with the existing Unity sensor/actuator controllers.

  Create `DT Unity/Assets/Scripts/AAS/IAASDriver.cs` with the following content:
  ```csharp
  using System.Collections;
  using UnityEngine;
  using UnityEngine.Networking;

  public interface IAASDriver
  {
      void WriteActuator(string pinId, bool value);
      bool ReadSensor(string pinId);
  }

  public class AASHttpDriver : IAASDriver
  {
      private AASSensorController sensorController;
      private AASActuatorController actuatorController;
      private string baseServerUrl;
      private string pinsSubmodelId;

      public AASHttpDriver(AASSensorController sensorCtrl, AASActuatorController actuatorCtrl, string serverUrl, string pinsSmId)
      {
          this.sensorController = sensorCtrl;
          this.actuatorController = actuatorCtrl;
          this.baseServerUrl = serverUrl;
          this.pinsSubmodelId = pinsSmId;
      }

      public bool ReadSensor(string pinId)
      {
          // Read from local cache for instant zero-latency physics response
          if (sensorController != null)
          {
              var proxy = sensorController.GetComponentInChildren<AASSensorController.SensorPhysicsProxy>();
              // Search in proxies for the matching pinId
              var proxies = Object.FindObjectsByType<AASSensorController.SensorPhysicsProxy>(FindObjectsSortMode.None);
              foreach (var p in proxies)
              {
                  if (p.binding != null && p.binding.pinId == pinId)
                  {
                      return p.binding.lastState;
                  }
              }
          }
          return false;
      }

      public void WriteActuator(string pinId, bool value)
      {
          // 1. Instantly update the local simulation actuator to eliminate latency
          if (actuatorController != null)
          {
              foreach (var b in actuatorController.bindings)
              {
                  if (b.pinId == pinId)
                  {
                      b.currentState = value;
                  }
              }
          }

          // 2. Fire-and-forget HTTP PUT request to sync the state back to BaSyx
          string encodedPinsId = System.Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(pinsSubmodelId))
              .Replace("+", "-").Replace("/", "_").TrimEnd('=');
          string url = $"{baseServerUrl}/submodels/{encodedPinsId}/submodel-elements/Inputs.{pinId}";
          string json = $"{{\"idShort\":\"{pinId}\",\"modelType\":\"Property\",\"valueType\":\"xs:boolean\",\"value\":\"{value.ToString().ToLower()}\"}}";
          
          StaticCoroutineRunner.Start(SyncActuatorToAASRoutine(url, json));
      }

      private IEnumerator SyncActuatorToAASRoutine(string url, string json)
      {
          using (UnityWebRequest req = new UnityWebRequest(url, "PUT"))
          {
              byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
              req.uploadHandler = new UploadHandlerRaw(bodyRaw);
              req.downloadHandler = new DownloadHandlerBuffer();
              req.SetRequestHeader("Content-Type", "application/json");
              req.timeout = 2;
              yield return req.SendWebRequest();
          }
      }
  }

  // Helper utility to launch coroutines from non-MonoBehaviour classes
  public class StaticCoroutineRunner : MonoBehaviour
  {
      private static StaticCoroutineRunner instance;
      public static void Start(IEnumerator routine)
      {
          if (instance == null)
          {
              GameObject obj = new GameObject("StaticCoroutineRunner");
              instance = obj.AddComponent<StaticCoroutineRunner>();
              Object.DontDestroyOnLoad(obj);
          }
          instance.StartCoroutine(routine);
      }
  }
  ```

- [ ] **Step 3.2: Commit the driver interface**
  ```bash
  git add "DT Unity/Assets/Scripts/AAS/IAASDriver.cs"
  git commit -m "feat: add IAASDriver and AASHttpDriver for real-time logic execution"
  ```

---

### Task 4: Implement Unity Rule Engine (`AASRuleEngine.cs`)

**Files:**
- Create: `DT Unity/Assets/Scripts/AAS/AASRuleEngine.cs`

- [ ] **Step 4.1: Write the C# rule engine parser & coroutine logic**
  Create the rule engine that downloads the JSON from BaSyx, parses it using `Newtonsoft.Json`, and runs the start and triggered sequences in Coroutines.

  Create `DT Unity/Assets/Scripts/AAS/AASRuleEngine.cs` with the following content:
  ```csharp
  using System;
  using System.Collections;
  using System.Collections.Generic;
  using System.Linq;
  using UnityEngine;
  using UnityEngine.Networking;
  using Newtonsoft.Json.Linq;

  public class AASRuleEngine : MonoBehaviour
  {
      private IAASDriver driver;
      private string rulesUrl;
      private bool isInitialized = false;

      // Logic rules classes
      private JArray startSteps;
      private JArray sequences;
      private HashSet<string> activeSequences = new HashSet<string>();

      public void Init(string serverUrl, string controlLogicSubmodelId, IAASDriver aasDriver)
      {
          this.driver = aasDriver;
          string encodedSubmodelId = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(controlLogicSubmodelId))
              .Replace("+", "-").Replace("/", "_").TrimEnd('=');
          this.rulesUrl = $"{serverUrl}/submodels/{encodedSubmodelId}/submodel-elements/Rules";

          StartCoroutine(FetchAndStartRulesRoutine());
      }

      private IEnumerator FetchAndStartRulesRoutine()
      {
          Debug.Log($"[RuleEngine] 🔄 Fetching rules from {rulesUrl}");
          UnityWebRequest req = UnityWebRequest.Get(rulesUrl);
          yield return req.SendWebRequest();

          if (req.result != UnityWebRequest.Result.Success)
          {
              Debug.LogWarning($"[RuleEngine] ⚠️ No logic rules found or failed to fetch: {req.error}");
              yield break;
          }

          try
          {
              JObject root = JObject.Parse(req.downloadHandler.text);
              string rulesJsonStr = root["value"]?.ToString();
              if (string.IsNullOrEmpty(rulesJsonStr))
              {
                  // Try reading direct result/value if structure is raw
                  rulesJsonStr = root.ToString();
              }

              JObject rules = JObject.Parse(rulesJsonStr);
              startSteps = rules["start"] as JArray;
              sequences = rules["sequences"] as JArray;

              Debug.Log($"[RuleEngine] 📜 Rules loaded. Start actions: {startSteps?.Count ?? 0}, Sequences: {sequences?.Count ?? 0}");

              isInitialized = true;

              // Run Start Sequence
              if (startSteps != null && startSteps.Count > 0)
              {
                  StartCoroutine(ExecuteSequenceRoutine("Start", startSteps));
              }

              // Begin evaluation loop
              StartCoroutine(TriggerEvaluationLoop());
          }
          catch (Exception e)
          {
              Debug.LogError($"[RuleEngine] ❌ Error parsing rules JSON: {e.Message}");
          }
      }

      private IEnumerator TriggerEvaluationLoop()
      {
          while (isInitialized)
          {
              if (sequences != null)
              {
                  foreach (JObject seq in sequences)
                  {
                      string name = seq["name"]?.ToString() ?? "UnnamedSequence";
                      if (activeSequences.Contains(name)) continue;

                      JObject trigger = seq["trigger"] as JObject;
                      if (trigger != null && EvaluateTrigger(trigger))
                      {
                          JArray steps = seq["steps"] as JArray;
                          if (steps != null)
                          {
                              StartCoroutine(ExecuteSequenceRoutine(name, steps));
                          }
                      }
                  }
              }
              yield return new WaitForSeconds(0.1f); // Check triggers every 100ms
          }
      }

      private bool EvaluateTrigger(JObject trigger)
      {
          string op = trigger["operator"]?.ToString() ?? "AND";
          JArray conditions = trigger["conditions"] as JArray;
          if (conditions == null || conditions.Count == 0) return false;

          bool andResult = true;
          bool orResult = false;

          foreach (JObject cond in conditions)
          {
              string sensor = cond["sensor"]?.ToString();
              bool targetVal = cond["value"]?.ToObject<bool>() ?? true;
              bool actualVal = driver.ReadSensor(sensor);

              bool matches = (actualVal == targetVal);
              andResult &= matches;
              orResult |= matches;
          }

          return op.Equals("OR", StringComparison.OrdinalIgnoreCase) ? orResult : andResult;
      }

      private IEnumerator ExecuteSequenceRoutine(string seqName, JArray steps)
      {
          activeSequences.Add(seqName);
          Debug.Log($"[RuleEngine] 🚀 Starting sequence: '{seqName}'");

          foreach (JObject step in steps)
          {
              string type = step["type"]?.ToString();
              if (type == "set_actuator")
              {
                  string actuator = step["actuator"]?.ToString();
                  bool value = step["value"]?.ToObject<bool>() ?? false;
                  driver.WriteActuator(actuator, value);
                  Debug.Log($"[RuleEngine] [{seqName}] Action: Set actuator '{actuator}' to {value}");
              }
              else if (type == "wait_time")
              {
                  float seconds = step["seconds"]?.ToObject<float>() ?? 0f;
                  Debug.Log($"[RuleEngine] [{seqName}] Action: Waiting {seconds}s");
                  yield return new WaitForSeconds(seconds);
              }
              else if (type == "wait_until")
              {
                  string op = step["operator"]?.ToString() ?? "AND";
                  JArray conditions = step["conditions"] as JArray;
                  
                  // Support old fallback schema with single sensor
                  if (conditions == null || conditions.Count == 0)
                  {
                      string sensor = step["sensor"]?.ToString();
                      if (!string.IsNullOrEmpty(sensor))
                      {
                          bool targetVal = step["value"]?.ToObject<bool>() ?? true;
                          conditions = new JArray(new JObject { { "sensor", sensor }, { "value", targetVal } });
                      }
                  }

                  if (conditions != null && conditions.Count > 0)
                  {
                      Debug.Log($"[RuleEngine] [{seqName}] Action: Waiting until condition matching '{op}'");
                      bool satisfied = false;
                      while (!satisfied)
                      {
                          bool andResult = true;
                          bool orResult = false;

                          foreach (JObject cond in conditions)
                          {
                              string sensor = cond["sensor"]?.ToString();
                              bool targetVal = cond["value"]?.ToObject<bool>() ?? true;
                              bool actualVal = driver.ReadSensor(sensor);
                              bool matches = (actualVal == targetVal);
                              
                              andResult &= matches;
                              orResult |= matches;
                          }

                          satisfied = op.Equals("OR", StringComparison.OrdinalIgnoreCase) ? orResult : andResult;
                          if (!satisfied) yield return null; // wait for next frame
                      }
                  }
              }
          }

          Debug.Log($"[RuleEngine] ✅ Sequence complete: '{seqName}'");
          activeSequences.Remove(seqName);
      }
  }
  ```

- [ ] **Step 4.2: Commit the Unity rule engine script**
  ```bash
  git add "DT Unity/Assets/Scripts/AAS/AASRuleEngine.cs"
  git commit -m "feat: add AASRuleEngine logic parser and coroutine sequence executor"
  ```

---

### Task 5: Integrate `AASRuleEngine` in `BaSyxManager`

**Files:**
- Modify: `DT Unity/Assets/Scripts/BaSyxManager.cs`

- [ ] **Step 5.1: Detect and Initialize the Rule Engine**
  Update `BaSyxManager.cs` in `ProcessRobot` and `SyncKitLoop` to:
  1. Detect the `ControlLogic` submodel descriptor in the AAS submodel descriptors.
  2. If found, add the `AASRuleEngine` component to the instantiated robot GameObject.
  3. Initialize `AASRuleEngine` passing the BaSyx repository URL, the `ControlLogic` submodel ID, and an instance of `AASHttpDriver` referencing the robot's `AASSensorController` and `AASActuatorController`.

  Let's look at `BaSyxManager.cs` line 320 to see where controllers are setup:
  ```csharp
  // Around line 327:
  if (pinSubmodelId != null && behSubmodelId != null) {
      // existing initialization
  }
  ```
  We will add detection for `controlLogicSubmodelId` and run:
  ```csharp
  if (controlLogicSubmodelId != null) {
      var engine = robotGo.AddComponent<AASRuleEngine>();
      var driver = new AASHttpDriver(sensorCtrl, actuatorCtrl, aasServerUrl, pinSubmodelId);
      engine.Init(aasServerUrl, controlLogicSubmodelId, driver);
  }
  ```

- [ ] **Step 5.2: Commit the integration**
  ```bash
  git add "DT Unity/Assets/Scripts/BaSyxManager.cs"
  git commit -m "feat: integrate AASRuleEngine initialization inside BaSyxManager"
  ```

---

### Verification and Testing

1. Run the `conveyor_wizard.py` to configure a kit, build logic rules (start and triggers), and deploy to the local BaSyx server.
2. Verify the AAS contains the `ControlLogic` submodel with the correctly formatted `Rules` JSON property.
3. Start Unity, play the scene, and ensure `BaSyxManager` discovers the kit, runs the start calibration steps, and successfully triggers sequences when physics/simulated sensors toggle state.
