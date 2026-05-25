using UnityEngine;
using System.Collections.Generic;
using System.Linq;

public class RobotCameraManager : MonoBehaviour
{
    public static RobotCameraManager Instance { get; private set; }

    [Header("Targeting")]
    public List<Transform> targets = new List<Transform>();
    
    [Header("Framing & Orbit")]
    public bool enableRotation = true;
    public float rotationSpeed = 10f;
    [Range(10f, 85f)] public float verticalAngle = 45f;
    public float distanceMultiplier = 2.0f;
    public float minDistance = 5f;

    [Header("Smoothness")]
    public float smoothSpeed = 4f;

    private float currentHorizontalAngle = 0f;
    private Camera mainCam;
    private Vector3 currentVelocity = Vector3.zero;

    void Awake()
    {
        if (Instance == null) Instance = this;
        else { Destroy(gameObject); return; }

        mainCam = Camera.main;
    }

    void LateUpdate()
    {
        if (targets.Count == 0 || mainCam == null) return;

        // 1. Limpar targets nulos
        targets = targets.Where(t => t != null).ToList();
        if (targets.Count == 0) return;

        // 2. Calcular o centro baseado APENAS nas bases (transforms raiz)
        // Isso evita que a câmara acompanhe o movimento dos braços
        Vector3 center = Vector3.zero;
        Bounds baseBounds = new Bounds(targets[0].position, Vector3.one * 0.1f);
        
        foreach (var t in targets)
        {
            center += t.position;
            baseBounds.Encapsulate(t.position);
        }
        center /= targets.Count;

        // 3. Rotação Horizontal
        if (enableRotation && Application.isPlaying)
        {
            currentHorizontalAngle += rotationSpeed * Time.deltaTime;
        }

        // 4. Calcular Distância baseada no espalhamento das bases
        float maxDim = Mathf.Max(baseBounds.size.x, baseBounds.size.z);
        float distance = Mathf.Max(minDistance, maxDim * distanceMultiplier);

        // 5. Coordenadas Esféricas
        float horizRad = currentHorizontalAngle * Mathf.Deg2Rad;
        float vertRad = verticalAngle * Mathf.Deg2Rad;

        float x = distance * Mathf.Cos(vertRad) * Mathf.Sin(horizRad);
        float y = distance * Mathf.Sin(vertRad);
        float z = distance * Mathf.Cos(vertRad) * Mathf.Cos(horizRad);

        Vector3 targetCameraPos = center + new Vector3(x, y, z);

        // 6. Aplicar com suavidade
        mainCam.transform.position = Vector3.SmoothDamp(mainCam.transform.position, targetCameraPos, ref currentVelocity, 1f / smoothSpeed);
        mainCam.transform.LookAt(center);
    }

    public void AddTarget(Transform target)
    {
        if (!targets.Contains(target)) {
            targets.Add(target);
            Debug.Log($"[Robot-Camera] Base registered: {target.name}");
        }
    }

    public void RemoveTarget(Transform target)
    {
        targets.Remove(target);
    }
}
