# Robot Model Setup

## Overview

The MuJoCo simulator uses robot models defined in XML format. The system includes a default simple 3-DOF arm model with cleaning props.

## Default Model: `simple_arm`

The default model (`models/simple_arm.xml`) includes:

- **Robot Arm**: 3-DOF manipulator with:
  - Base (gray cylinder) - fixed to ground
  - Link 1 (red) - rotates around vertical axis
  - Link 2 (green) - shoulder joint
  - Link 3 (blue) - elbow joint
  - End effector with cleaning tool (yellow sponge/brush)

- **Cleaning Environment**:
  - Ground plane (light gray)
  - Cleaning surface/table (blue-gray) at position (0.4, 0, 0.15)
  - Proper lighting for visualization

## Model Structure

```
base (fixed)
  └── link1 (joint1: rotation around Z)
      └── link2 (joint2: shoulder pitch)
          └── link3 (joint3: elbow pitch)
              └── tool (cleaning sponge/brush)
```

## Using Custom Models

### Option 1: Place XML file in `models/` directory

1. Create your robot model XML file
2. Place it in `models/` directory
3. Update `ROBOT_MODELS` in `src/robot/mujoco_simulator.py`:

```python
ROBOT_MODELS = {
    "your_robot": {
        "model_path": "models/your_robot.xml",
        "description": "Your robot description",
        "dof": 6,  # Number of degrees of freedom
        "gripper": False,
    },
}
```

4. Use it:
```python
simulator = MuJoCoSimulator(robot_model="your_robot")
```

### Option 2: Use custom path

```python
simulator = MuJoCoSimulator(
    robot_model="simple_arm",
    model_path=pathlib.Path("path/to/your/model.xml")
)
```

## Model Requirements

Your robot model XML should:

1. **Define joints properly**: Each joint should have:
   - `type`: "hinge", "slide", etc.
   - `axis`: Rotation/translation axis
   - `range`: Joint limits (optional but recommended)
   - `damping`: Joint damping (optional, helps stability)

2. **Define actuators**: Motors or other actuators to control joints:
   ```xml
   <actuator>
       <motor name="motor1" joint="joint1" gear="100"/>
   </actuator>
   ```

3. **Include cleaning props** (optional but recommended):
   - A cleaning surface/table to interact with
   - A tool attached to the end effector
   - Proper contact settings (`contype`, `conaffinity`)

4. **Set up materials** (optional but improves visualization):
   ```xml
   <asset>
       <material name="robot_mat" rgba="0.9 0.2 0.2 1"/>
   </asset>
   ```

## Example: Adding More Cleaning Props

To add more cleaning props to the scene:

```xml
<worldbody>
    <!-- Existing robot and surface -->
    
    <!-- Add a cleaning bottle -->
    <body name="bottle" pos="0.3 0.2 0.2">
        <geom type="cylinder" size="0.02 0.08" rgba="0.8 0.8 0.2 1"/>
    </body>
    
    <!-- Add a bucket -->
    <body name="bucket" pos="-0.3 0 0.1">
        <geom type="cylinder" size="0.1 0.15" rgba="0.5 0.5 0.5 1"/>
    </body>
</worldbody>
```

## Troubleshooting

**Model not loading?**
- Check XML syntax (valid XML)
- Verify file path is correct
- Check MuJoCo XML schema compliance

**Robot not visible?**
- Check initial joint positions (may be out of view)
- Verify geometry sizes are reasonable
- Check camera position in viewer

**Robot not moving?**
- Verify actuators are defined
- Check joint names match actuator joint references
- Ensure control ranges are appropriate

**No contact with surface?**
- Set `contype="1"` and `conaffinity="1"` on geometries that should contact
- Check geometry positions overlap
- Verify contact settings in both robot and surface

## Advanced: Using MuJoCo Assets

You can use MuJoCo's built-in assets or download models from:

- [MuJoCo Model Zoo](https://github.com/google-deepmind/mujoco/tree/main/model)
- [RoboSuite Models](https://robosuite.ai/)
- Create custom models using [MuJoCo XML Reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html)

## Next Steps

- Customize the cleaning surface size/position
- Add more cleaning tools (different brushes, sponges)
- Create different robot models (6-DOF, 7-DOF arms)
- Add objects to clean (dirty surfaces, stains)

