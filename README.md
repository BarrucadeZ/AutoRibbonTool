# Auto Ribbon Tool
## How to Use
- Download AutoRibbonTool.py and Ultimate_Ribbon_Rig_Generator.ui
- Drag the .ui file to ...\Documents\maya\scripts
- Run the .py file in Maya script editor
## Overview
This tool simplifies the process of creating and animating tentacles in Maya. It offers procedural controls, dynamic effects, and easy customization to match the desired look and behavior.

## Features

### 1. Curve-Based Joint Creation
- Users can generate a **NURBS curve** and edit its shape to match the model.
- The tool creates a **joint chain** along the curve based on the assigned joint count, complete with **FK controls**.

### 2. Roll Module
- Adjust the **roll parameter** to control the rotation of each FK control.
- The tentacle **curls gradually**, starting from the tip, for natural rolling effects.

### 3. Ripple Module
- Utilizes a **MASH distribution node** to create a ripple-like scaling effect along the joint chain.
- The scaling effect propagates from the chain's start to its end.

### 4. Ribbon and Deformers
- A procedurally created **ribbon system** adds flexibility to the tentacle.
- Includes dynamic deformers for:
  - **Swinging** along a sine curve.
  - **Twisting** along the main axis.

## Usage
1. Generate and edit the **NURBS curve** to match the tentacle shape.
2. Assign the **joint count** and create the joint chain with FK controls.
3. Use the **Roll Module** to adjust curling effects.
4. Apply the **Ripple Module** for dynamic scaling animations.
5. Fine-tune the tentacle motion with the ribbon system and deformers for swinging and twisting.
