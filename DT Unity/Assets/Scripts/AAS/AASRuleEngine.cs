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
        this.rulesUrl = $"{serverUrl}/submodels/{Base64Url(controlLogicSubmodelId)}/submodel-elements/Rules";

        StartCoroutine(FetchAndStartRulesRoutine());
    }

    private IEnumerator FetchAndStartRulesRoutine()
    {
        Debug.Log($"[RuleEngine] 🔄 Fetching rules from {rulesUrl}");
        using (UnityWebRequest req = UnityWebRequest.Get(rulesUrl))
        {
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
                    Debug.Log($"[RuleEngine] [{seqName}] Action: Wait until condition matching '{op}'");
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

    private string Base64Url(string i)
    {
        if (string.IsNullOrEmpty(i)) return "";
        return Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(i))
            .Replace("+", "-")
            .Replace("/", "_")
            .TrimEnd('=');
    }
}
