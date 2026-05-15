# Design Doc: Lerp Smoothing for AAS Robot Sync

Date: 2026-05-15
Topic: Smoothing "flickery" movement in Unity Digital Twin

## Problem
The current implementation of `AASRobotSync.cs` applies rotations directly when data is received from the AAS (polling at 20Hz). Since the data source updates at 10Hz and network latency varies, the robot "snaps" to new positions, causing a flickery/jittery visual effect.

## Solution
Implement a frame-based interpolation (Lerp) to decouple visual movement from network updates.

## Architecture & Implementation

### 1. Data Structure Update
Modify `JointData` struct in `AASRobotSync.cs` to track:
- `targetAngle`: The last value received from AAS.
- `currentAngle`: The interpolated value currently applied to the transform.

### 2. Logic Split
- **Networking (`SyncFromAASLiveJoints`)**: Updates `targetAngle`.
- **Animation (`Update`)**: Smoothly interpolates `currentAngle` towards `targetAngle` using `Mathf.LerpAngle` and applies the rotation to the transform.

### 3. Parameters
- `lerpSpeed` (float): Configurable via Unity Inspector to control smoothing intensity (default: 15f).

## Validation Plan
- Verify that `AASRobotSync.cs` compiles.
- Check that movement is visibly smoother in Unity.
- Ensure that the robot still reaches the correct final orientations.
