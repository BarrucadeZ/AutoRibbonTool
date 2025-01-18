import os
from PySide6 import QtCore, QtGui, QtWidgets, QtUiTools
from PySide6.QtCore import QFile

uiFilePath = os.path.join(os.path.expanduser("~"), "Documents", "maya", "scripts", "Ultimate_Ribbon_Rig_Generator_v2.ui")

def loadUi(uiFilePath):
    uiFile = QtCore.QFile(uiFilePath)
    uiFile.open(QtCore.QFile.ReadOnly)
    uiWindow = QtUiTools.QUiLoader().load(uiFile)
    uiFile.close()
    return uiWindow

class MainWindow():
    def __init__(self, parent=None):
        self.ui = loadUi(uiFilePath)
        self.ui.show()

        #Button
        self.ui.Button_Curve.clicked.connect(self.uiCreateRibbonCurve)
        self.ui.Button_RibbonRig.clicked.connect(self.uiCreateRibbonRig)

        #Values
        self.uiJointCount = self.ui.Slider_JointCount.value()
        self.ui.Slider_JointCount.valueChanged.connect(self.updateJointCount)
        #self.uiTentacleLength = str(self.ui.LineEdit_CurveLength.text())
        self.uiTentacleLength = self.ui.Spinbox_CurveLength.value()
        self.ui.Spinbox_CurveLength.valueChanged.connect(self.updateTentacleLength)

    def updateJointCount(self, jointCountValue):
        self.uiJointCount = jointCountValue
    
    def updateTentacleLength(self, tentacleLengthValue):
        self.uiTentacleLength = tentacleLengthValue

    def uiCreateRibbonCurve(self):
        tentacle = Tentacle(
        modelName="tentacle",
        jointCount=self.uiJointCount,
        tentacleLength=self.uiTentacleLength,
        isAutoMeasureLength=True,
        primaryAxis='y',
        secondaryAxis='z',
        rollAxis='x',
        drvCtrl="CTRL_M_TentacleDrv_001"
    )
        tentacle.createRibbonCurve()

    def uiCreateRibbonRig(self):
        tentacle = Tentacle(
        modelName="tentacle",
        jointCount=self.uiJointCount,
        tentacleLength=self.uiTentacleLength,
        isAutoMeasureLength=True,
        primaryAxis='y',
        secondaryAxis='z',
        rollAxis='x',
        drvCtrl="CTRL_M_TentacleDrv_001"
    )
        tentacle.setUpTentacleFK()
        tentacle.tentacleRoll()
        tentacle.tentacleRipple()
        tentacle.tentacleRibbonDeformer()
        

if __name__ == "__main__":
    mainWindow = MainWindow()

import maya.cmds as cmds
class Tentacle:

    def __init__(self, modelName, jointCount, tentacleLength, isAutoMeasureLength, primaryAxis='y', secondaryAxis='x', rollAxis='z',
                 axisVector=(0, 1, 0), CTRL_COLOR={'l': 18, 'm': 14, 'r': 20}, 
                 ribbonCurve="crv_ribbon", surface='surface_ribbon', 
                 drvCtrl="CTRL_M_TentacleDrv_001",
                 model="tentacle"):
        self.modelName = modelName
        self.jointCount = jointCount
        self.tentacleLength = tentacleLength
        self.isAutoMeasureLength = isAutoMeasureLength
        self.primaryAxis = primaryAxis
        self.secondaryAxis = secondaryAxis
        self.rollAxis = rollAxis

        self.axisVector = axisVector
        self.CTRL_COLOR = CTRL_COLOR

        self.ribbonCurve = ribbonCurve
        self.surface = surface

        self.drvCtrl = drvCtrl

        self.model = model

        if self.primaryAxis not in ['x', 'y', 'z'] or self.secondaryAxis not in ['x', 'y', 'z']:
            cmds.error("Axes must be 'x', 'y', or 'z'.")
        if self.primaryAxis == self.secondaryAxis:
            cmds.error("Primary axis and secondary axis must be different.")

    def createRibbonCurve(self):
        # Axis vector for curve direction and joint placement
        self.axisVector = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[self.primaryAxis]

        # Calculate positions for curve CVs
        cvPositions = []
        step = self.tentacleLength / float(self.jointCount - 1)  # Five CVs, four segments
        for i in range(self.jointCount):
            position = [v * step * i for v in self.axisVector]
            cvPositions.append(position)

        # Create the NURBS curve
        crvName = "crv_ribbon"
        self.ribbonCurve = cmds.curve(name=crvName, p=cvPositions, d=1)  # Degree 1 for a straight curve
        cmds.select(clear=True)

    def setUpTentacleFK(self):
        # Axis vector for curve direction and joint placement
        self.axisVector = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[self.primaryAxis]

        # Set up curve to form ribbon
        ribbonGroup = cmds.group(empty=True, name="ribbon_Group")
        cmds.parent(self.ribbonCurve, ribbonGroup)

        # Duplicate the curve and create ribbon
        ribbonCurveDup = cmds.duplicate(self.ribbonCurve)[0]
        cmds.setAttr(self.ribbonCurve + '.translate{}'.format(self.secondaryAxis.upper()), 10)
        cmds.setAttr(ribbonCurveDup + '.translate{}'.format(self.secondaryAxis.upper()), -10)

        self.surface = \
        cmds.loft(ribbonCurveDup, self.ribbonCurve, constructionHistory=False, uniform=True, degree=3, sectionSpans=1,
                  range=False, polygon=0,
                  name='surface_ribbon')[0]
        cmds.parent(self.surface, ribbonGroup)

        surfaceShape = cmds.listRelatives(self.surface, shapes=True)[0]

        # delete or hide ribbon curves and hide ribbon surface
        cmds.setAttr(self.ribbonCurve + '.visibility', 0)
        cmds.setAttr(ribbonCurveDup + '.visibility', 0)
        cmds.setAttr(self.surface + '.visibility', 0)


        # Create follicle group
        follicleGroup = cmds.group(empty=True, name="follicle_Group")

        # Calculate length per segment
        if self.isAutoMeasureLength:
            lengthPerSegment = self.tentacleLength / self.jointCount
        else:
            lengthPerSegment = self.tentacleLength

        # Create joints and place the first joint in a joint group
        jointGroup = cmds.group(empty=True, name=f"{self.modelName}_jointGroup")
        joints = []
        jointZeroGroups = []
        previousJoint = None

        drvJoints = []

        for i in range(self.jointCount):
            # create follicles
            follicleShape = cmds.createNode('follicle', name="follicleShape_m_tentacle_{:03d}".format(i + 1))

            # rename follicle transform node
            follicle = cmds.listRelatives(follicleShape, parent=True)[0]
            follicleName = follicle.replace("follicleShape", "follicle")
            follicle = cmds.rename(follicle, follicleName)

            cmds.parent(follicle, follicleGroup)

            # Connect Follicle
            cmds.connectAttr(surfaceShape + '.worldSpace[0]', follicleShape + '.inputSurface')
            # connect follicle shape to transofrm
            cmds.connectAttr(follicleShape + '.outTranslate', follicle + '.translate')
            cmds.connectAttr(follicleShape + '.outRotate', follicle + '.rotate')
            # Set UV value
            cmds.setAttr(follicleShape + '.parameterU', 0.5)
            cmds.setAttr(follicleShape + '.parameterV', float(i) / (self.jointCount - 1))

            # Calculate joint position
            position = [v * lengthPerSegment * i for v in self.axisVector]

            # Create joint
            jointName = "jnt_m_tentacle_{:03d}".format(i + 1)
            joint = cmds.joint(position=position, name=jointName)

            # Rotate the joint
            if self.primaryAxis == 'x':
                cmds.setAttr(joint + '.rotateY', 90)
            elif self.primaryAxis == 'z':
                cmds.setAttr(joint + '.rotateX', 90)
            else:
                cmds.setAttr(joint + '.rotate', 0, 0, 0)

            cmds.makeIdentity(joint, apply=True, rotate=True)

            # if i<self.jointCount-1:
            joints.append(joint)

            jointZeroGroup = cmds.group(joint, name=f"Zero_{jointName}")
            cmds.parent(joint, jointZeroGroup)

            jointZeroGroups.append(jointZeroGroup)

            # Parent the first joint to the joint group
            # if i == 0:
            if cmds.listRelatives(jointZeroGroup, parent=True) != [jointGroup]:
                cmds.parent(jointZeroGroup, jointGroup)

            # Create Driver Joint to bind ribbon surface and control it
            cmds.select(clear=True)
            drvJointName = "drv_jnt_m_tentacle_{:03d}".format(i + 1)
            drvJoint = cmds.joint(position=position, name=drvJointName)

            # Rotate the joint
            if self.primaryAxis == 'x':
                cmds.setAttr(drvJoint + '.rotateY', 90)
            elif self.primaryAxis == 'z':
                cmds.setAttr(drvJoint + '.rotateX', 90)
            else:
                cmds.setAttr(drvJoint + '.rotate', 0, 0, 0)

            cmds.makeIdentity(drvJoint, apply=True, rotate=True)

            drvJoints.append(drvJoint)
            cmds.parent(drvJoint, jointGroup)

            # Move joint to follicle's position and use follicle to constraint it
            cmds.delete(cmds.parentConstraint(follicle, jointZeroGroup, maintainOffset=False))
            cmds.parentConstraint(follicle, joint, maintainOffset=True)

            #
            cmds.delete(cmds.parentConstraint(follicle, drvJoint, maintainOffset=False))

            # Make the next joint not the child of this joint (for ribbon setting, the existence of parent relation has no influence on FK)
            cmds.select(clear=True)

            # Parent the current joint to the previous joint
            # if previousJoint:
            # if cmds.listRelatives(joint, parent=True) != [previousJoint]:
            # cmds.parent(joint, previousJoint)

            # previousJoint = joint

        # Set orient joint for all joints
        #orientString = f"{self.primaryAxis}{''.join([x for x in ['x', 'y', 'z'] if x != self.primaryAxis and x != self.secondaryAxis])}{self.secondaryAxis}"
        #for joint in joints:
            #cmds.joint(joint, edit=True, orientJoint=orientString, zeroScaleOrient=True)

        #for drvJoint in drvJoints:
            #cmds.joint(drvJoint, edit=True, orientJoint=orientString, zeroScaleOrient=True)

        # Create controllers and groups
        ctrls = []
        ctrlGroups = []
        for i, drvJoint in enumerate(drvJoints):
            if i < len(drvJoints) - 1:
                ctrlName = drvJoint.replace("jnt", "ctrl")

                # Add PlaceHolder Extra FK Ctrls
                if i%4 != 0: 
                    ctrl = cmds.circle(name=ctrlName, normal=self.axisVector, radius=lengthPerSegment / 1.0)[0]
                    cmds.setAttr(f"{ctrl}.overrideEnabled", 1)
                    cmds.setAttr(f"{ctrl}.overrideColor", self.CTRL_COLOR['m'])
                else:
                    ctrl = createSquareCurve(name = ctrlName, size=lengthPerSegment / 0.5)
                    cmds.setAttr(f"{ctrl}.overrideEnabled", 1)
                    cmds.setAttr(f"{ctrl}.overrideColor", self.CTRL_COLOR['l'])

                ctrlGroup = cmds.group(ctrl, name=f"{ctrlName}_grp")
                ctrls.append(ctrl)
                ctrlGroups.append(ctrlGroup)

                # Match controller group to joint
                cmds.delete(cmds.parentConstraint(drvJoint, ctrlGroup))
                # cmds.makeIdentity(ctrlGroup, apply=True, rotate=True)

                # Parent constraint controller to joint
                cmds.parentConstraint(ctrl, drvJoint, maintainOffset=True)
                cmds.scaleConstraint(ctrl, drvJoint)  # This only take effect in the scale of primary axis


            # Use the last ctrl to constraint the final joint besides the previous joint
            else:
                cmds.parentConstraint(ctrls[-1], drvJoint, maintainOffset=True)

        # Establish parent-child relationships between controller groups
        for i in range(1, len(ctrlGroups)):
            cmds.parent(ctrlGroups[i], ctrls[i - 1])

                

        # Put ctrl groups under main drvCtrl
        drvCtrlName = "CTRL_M_TentacleDrv_001"
        # self.drvCtrl = cmds.circle(name=drvCtrlName, normal=self.axisVector, radius= 100)[0]
        self.drvCtrl = createArrowCurve(name=drvCtrlName)
        cmds.setAttr(f"{self.drvCtrl}.overrideEnabled", 1)
        cmds.setAttr(f"{self.drvCtrl}.overrideColor", self.CTRL_COLOR['r'])

        cmds.setAttr(self.drvCtrl + '.scale', lengthPerSegment / 0.5, lengthPerSegment / 0.5, lengthPerSegment / 0.5)
        cmds.makeIdentity(self.drvCtrl, apply=True, scale=True)
        cmds.parent(ctrlGroups[0], self.drvCtrl)

        


        # Scale the other two axis by connecting main ctrl's scale to bind joint's group
        # for ctrl, jointZeroGroup in zip(ctrls, jointZeroGroups):
        # if cmds.objExists(ctrl) and cmds.objExists(jointZeroGroup):
        # for axis in 'xyz':
        # if axis!= self.primaryAxis:
        # cmds.connectAttr(ctrl + f'.scale{axis.upper()}', jointZeroGroup + f'.scale{axis.upper()}')

        for axis in 'xyz':
            if axis != self.primaryAxis:
                cmds.connectAttr(self.drvCtrl + f'.scale{axis.upper()}', jointGroup + f'.scale{axis.upper()}')

        cmds.select(clear=True)

        # Bind Driver Joints to the ribbon surface, then the follicle attached to surface will control "Joints" bound to model
        if cmds.objExists(self.surface) and all(cmds.objExists(drvJoint) for drvJoint in drvJoints):
            cmds.select(drvJoints)
            cmds.select(self.surface, add=True)
            cmds.skinCluster(toSelectedBones=True, name="ribbonSurfaceSkinCluster")

        joints.pop(-1)
        if cmds.objExists(self.surface) and all(cmds.objExists(joint) for joint in joints):
            cmds.select(joints)
            cmds.sets(name="bindJointSet")
            cmds.select(self.model, add=True)
            cmds.skinCluster(toSelectedBones=True, name="modelSkinCluster",
                             maximumInfluences=int(self.jointCount / 2.0))

        return drvJoints

    def tentacleRoll(self):


        # Add Roll Attribute
        cmds.addAttr(self.drvCtrl, longName='rollDivider', niceName='----- ROLL -----', attributeType='enum',
                     enumName='', keyable=False)
        cmds.setAttr(self.drvCtrl + '.rollDivider', channelBox=True, lock=True)
        cmds.addAttr(self.drvCtrl, longName='Roll', attributeType='float', minValue=0, maxValue=1, keyable=True)
        cmds.addAttr(self.drvCtrl, longName='Angle', attributeType='float', defaultValue=-70, keyable=True)
        cmds.addAttr(self.drvCtrl, longName='Falloff', attributeType='float', minValue=0, maxValue=1, keyable=True)

        rollAttr = self.drvCtrl + '.Roll'
        angleAttr = self.drvCtrl + '.Angle'
        falloffAttr = self.drvCtrl + '.Falloff'

        # Use a multi node to reverse falloff value for subtraction
        mult = cmds.createNode('multDoubleLinear', name='mult_M_TentacleRollFalloffRvs_001')
        cmds.connectAttr(falloffAttr, mult + '.input1')
        cmds.setAttr(mult + '.input2', -1)
        falloffAttr = mult + '.output'

        # fkCtrls = cmds.ls('ctrl_m_tentacle_???', type = 'transform')
        fkCtrls = cmds.ls('drv_ctrl_m_tentacle_???', type='transform')
        fkCtrlNum = len(fkCtrls)

        # Create MASH distribute node
        distr = cmds.createNode('MASH_Distribute', name='distribute_M_TentacleRoll_001')
        cmds.setAttr(distr + '.pointCount', fkCtrlNum)

        # set Rotate in main axis to 1 to gather weight value from 0-1
        cmds.setAttr(distr + f'.rotate{self.rollAxis.upper()}', 1)
        # cmds.setAttr(distr + '.rotateX', 1)

        # Create breakout node
        breakout = cmds.createNode('MASH_Breakout', name='breakout_m_tentacleRoll_001')
        cmds.connectAttr(distr + '.outputPoints', breakout + '.inputPoints')

        # loop in each control to do the roll setup
        for i, fkCtrl in enumerate(fkCtrls):
            # get connect group
            # connect = fkCtrl.replace('ctrl_', 'connect_')
            connect = fkCtrl + '_grp'

            # create remap node to roll will only happen in the given section
            remap = cmds.createNode('remapValue', name='remap_m_tentacleRollWeight_{:03d}'.format(i + 1))

            # connect tentacle roll to remap
            cmds.connectAttr(rollAttr, remap + '.inputValue')
            # get max value by weight
            weightMax = 1 - float(i) / fkCtrlNum
            cmds.setAttr(remap + '.inputMax', weightMax)

            # get min value
            weightMin = 1 - float(i + 1) / fkCtrlNum
            # add node to subtract falloff so the joint can roll before the previous finshed
            add = cmds.createNode('addDoubleLinear', name='add_m_TentacleRollStart_{:03d}'.format(i + 1))
            cmds.setAttr(add + '.input1', weightMin)
            cmds.connectAttr(falloffAttr, add + '.input2')
            # clamp value so it wont go below 0
            clamp = cmds.createNode('clamp', name='clamp_m_TentacleRollStart_{:03d}'.format(i + 1))
            cmds.setAttr(clamp + '.maxR', 1)
            cmds.connectAttr(add + '.output', clamp + '.inputR')
            # connect with min value
            cmds.connectAttr(clamp + '.outputR', remap + '.inputMin')

            # multply divide node to mult remap weight with distribute weight to get the final roll weight for each joint
            # because MASH doesn't work with single axis, we need to use multiply divide to breakout single axis rotation
            multWeight = cmds.createNode('multiplyDivide', name='mult_m_TentacleRotWeight_{:03d}'.format(i + 1))
            cmds.connectAttr(remap + '.outValue', multWeight + '.input1X')
            cmds.connectAttr('{}.outputs[{}].rotate'.format(breakout, i), multWeight + '.input2')

            # mult with roll angle to get output
            multAngle = cmds.createNode('multDoubleLinear', name='mult_m_TentacleRotAngle_{:03d}'.format(i + 1))
            cmds.connectAttr(multWeight + '.outputX', multAngle + '.input1')
            cmds.connectAttr(angleAttr, multAngle + '.input2')

            # connect with connect group
            cmds.connectAttr(multAngle + '.output', connect + f'.rotate{self.rollAxis.upper()}')

    def tentacleRipple(self):

        # Add attrs
        cmds.addAttr(self.drvCtrl, longName='rippleDivider', niceName='----- RIPPLE -----', attributeType='enum',
                     enumName='', keyable=False)
        cmds.setAttr(self.drvCtrl + '.rippleDivider', channelBox=True, lock=True)
        cmds.addAttr(self.drvCtrl, longName='Ripple', attributeType='float', keyable=True)
        cmds.addAttr(self.drvCtrl, longName='RippleOut', attributeType='float', keyable=False)
        cmds.addAttr(self.drvCtrl, longName='RippleFrequency', attributeType='float', keyable=True, minValue=0,
                     defaultValue=5)
        cmds.addAttr(self.drvCtrl, longName='RippleAmplitude', attributeType='float', keyable=True, minValue=1,
                     defaultValue=1.5)
        cmds.addAttr(self.drvCtrl, longName='RippleOffset', attributeType='float', keyable=True)
        cmds.addAttr(self.drvCtrl, longName='RippleFalloff', attributeType='float', keyable=True, minValue=0,
                     maxValue=1, defaultValue=0.05)

        cmds.expression(string='{}.RippleOut = ({}.Ripple + {}.RippleOffset) % {}.RippleFrequency'.format(self.drvCtrl,
                                                                                                          self.drvCtrl,
                                                                                                          self.drvCtrl,
                                                                                                          self.drvCtrl),
                        name='expr_m_rippleOut_001')

        rippleAttr = self.drvCtrl + '.RippleOut'
        freqAttr = self.drvCtrl + '.RippleFrequency'
        ampAttr = self.drvCtrl + '.RippleAmplitude'
        offsetAttr = self.drvCtrl + '.RippleOffset'
        falloffAttr = self.drvCtrl + '.RippleFalloff'

        # remap ripple out to 0-1
        remap = cmds.createNode('remapValue', name='remap_m_tentacleRippleVal_001')
        cmds.connectAttr(rippleAttr, remap + '.inputValue')
        cmds.connectAttr(freqAttr, remap + '.inputMax')

        rippleAttr = remap + '.outValue'

        # use multDoubleLinear node to reverse falloff attr
        multRvs = cmds.createNode('multDoubleLinear', name='mult_m_tentacleRippleNeg_001')
        cmds.connectAttr(falloffAttr, multRvs + '.input1')
        cmds.setAttr(multRvs + '.input2', -1)
        falloffRvsAttr = multRvs + '.output'

        jnts = cmds.ls('jnt_m_tentacle_???', type='transform')
        jntsNum = len(jnts)

        # Create MASH distribute node
        distr = cmds.createNode('MASH_Distribute', name='distribute_m_tentacleRipple_001')
        cmds.setAttr(distr + '.pointCount', jntsNum)

        # connect scale with amplitude
        cmds.connectAttr(ampAttr, distr + '.scaleX')
        cmds.connectAttr(ampAttr, distr + '.scaleY')

        # create breakout node
        breakout = cmds.createNode('MASH_Breakout', name='breakout_m_tentacleRipple_001')
        cmds.connectAttr(distr + '.outputPoints', breakout + '.inputPoints')

        # loop in each joint
        unitVal = 1 / float(jntsNum + 1)
        for i, j in enumerate(jnts):
            # create remap node to do wave effect
            remapJnt = cmds.createNode('remapValue', name='remap_m_tentacleRipple_{:03d}'.format(i + 1))

            cmds.connectAttr(rippleAttr, remapJnt + '.inputValue')

            # set Remap Position
            cmds.setAttr(remapJnt + '.value[1].value_Position', (i + 0.5) * unitVal)
            cmds.setAttr(remapJnt + '.value[1].value_FloatValue', 1)
            cmds.setAttr(remapJnt + '.value[1].value_Interp', 2)

            # Set in and out point, default should be half unit
            addIn = cmds.createNode('addDoubleLinear', name='add_m_tentacleRippleIn_{:03d}'.format(i + 1))
            addOut = cmds.createNode('addDoubleLinear', name='add_m_tentacleRippleOut_{:03d}'.format(i + 1))

            cmds.setAttr(addIn + '.input1', i * unitVal)
            cmds.setAttr(addOut + '.input1', (i + 1) * unitVal)

            cmds.connectAttr(falloffRvsAttr, addIn + '.input2')
            cmds.connectAttr(falloffAttr, addOut + '.input2')

            # clamp the output in 0-1
            clamp = cmds.createNode('clamp', name='clamp_m_tentacleRipple_{:03d}'.format(i + 1))
            cmds.connectAttr(addIn + '.output', clamp + '.inputR')
            cmds.connectAttr(addOut + '.output', clamp + '.inputG')
            cmds.setAttr(clamp + '.maxR', 1)
            cmds.setAttr(clamp + '.maxG', 1)

            # connect clamp output to point position
            cmds.connectAttr(clamp + '.outputR', remapJnt + '.value[0].value_Position')
            cmds.setAttr(remapJnt + '.value[0].value_FloatValue', 0)
            cmds.setAttr(remapJnt + '.value[0].value_Interp', 2)
            cmds.connectAttr(clamp + '.outputG', remapJnt + '.value[2].value_Position')
            cmds.setAttr(remapJnt + '.value[2].value_FloatValue', 0)
            cmds.setAttr(remapJnt + '.value[2].value_Interp', 2)

            # connect output ripple weight with MASH distribute node
            blendRipple = cmds.createNode('blendColors', name='blend_m_tentacleRippleScale_{:03d}'.format(i + 1))
            cmds.connectAttr(remapJnt + '.outValue', blendRipple + '.blender')
            cmds.connectAttr('{}.outputs[{}].scale'.format(breakout, i), blendRipple + '.color1')
            cmds.setAttr(blendRipple + '.color2', 1, 1, 1)

            cmds.connectAttr(blendRipple + '.outputG', j + '.scaleX')
            cmds.connectAttr(blendRipple + '.outputB', j + '.scaleY')

    def tentacleRibbonDeformer(self):

        endDrvCtrlName = "CTRL_M_TentacleDrv_End_001"
        # endDrvCtrl = cmds.circle(name=endDrvCtrlName, normal=self.axisVector, radius=self.tentacleLength / 3.0)[0]
        endDrvCtrl = createSquareCurve(name=endDrvCtrlName, size=self.tentacleLength / 3.0)
        cmds.setAttr(f"{endDrvCtrl}.overrideEnabled", 1)
        cmds.setAttr(f"{endDrvCtrl}.overrideColor", self.CTRL_COLOR['r'])

        endDrvCtrlGroup = cmds.group(endDrvCtrl, name=f"{endDrvCtrlName}_grp")
        cmds.setAttr(f"{endDrvCtrlGroup}.translate{self.primaryAxis.upper()}", self.tentacleLength)

        # Put the ctrl into a group
        cmds.parent(endDrvCtrlGroup, self.drvCtrl)

        # Create a node group
        nodeGroup = cmds.createNode("transform", name=f"{self.modelName}_nodeGroup")

        ### Add Twist Deformer
        cmds.addAttr(self.drvCtrl, longName='twistDivider', niceName='----- TWIST -----', attributeType='enum',
                     enumName='', keyable=False)
        cmds.setAttr(self.drvCtrl + '.twistDivider', channelBox=True, lock=True)
        cmds.addAttr(self.drvCtrl, longName='Twist', attributeType='float', keyable=True)
        cmds.addAttr(endDrvCtrl, longName='Twist', attributeType='float', keyable=True)
        # Twist Deformer
        twistNode, twistHandle = cmds.nonLinear(self.surface, type='twist',
                                                name=self.surface.replace('surface', 'twist'))
        cmds.parent(twistHandle, nodeGroup)
        # Connect Twist Attr to drvCtrl and endDrvCtrl
        twistHandleShape = cmds.listRelatives(twistHandle, shapes=True)[0]
        cmds.connectAttr(self.drvCtrl + '.Twist', twistNode + '.endAngle')
        cmds.connectAttr(endDrvCtrl + '.Twist', twistNode + '.startAngle')

        ### Add Sine Deformer
        cmds.addAttr(self.drvCtrl, longName='sineDivider', niceName='----- SINE -----', attributeType='enum',
                     enumName='', keyable=False)
        cmds.setAttr(self.drvCtrl + '.sineDivider', channelBox=True, lock=True)
        cmds.addAttr(self.drvCtrl, longName='Amplitude', attributeType='float', keyable=True, minValue=0)
        cmds.addAttr(self.drvCtrl, longName='Wavelength', attributeType='float', keyable=True, minValue=0.1,
                     defaultValue=1)
        cmds.addAttr(self.drvCtrl, longName='Offset', attributeType='float', keyable=True)
        cmds.addAttr(self.drvCtrl, longName='SineRotation', attributeType='float', keyable=True)
        # Twist Deformer
        sineNode, sineHandle = cmds.nonLinear(self.surface, type='sine', name=self.surface.replace('surface', 'sine'))
        cmds.parent(sineHandle, nodeGroup)
        # Rotate the sine handle. if primary axis is Y, don't rotate the handle, if X, rotateZ = 90; if Z, rotateX = 90
        if self.primaryAxis == 'x':
            cmds.setAttr(sineHandle + '.rotate', 0, 0, 90)
        elif self.primaryAxis == 'z':
            cmds.setAttr(sineHandle + '.rotate', 90, 0, 0)
        else:
            cmds.setAttr(sineHandle + '.rotate', 0, 0, 0)

        cmds.setAttr(sineNode + '.dropoff', 1)
        # Connect Twist Attr to self.drvCtrl and endself.drvCtrl
        sineHandleShape = cmds.listRelatives(sineHandle, shapes=True)[0]
        cmds.connectAttr(self.drvCtrl + '.Amplitude', sineNode + '.amplitude')
        cmds.connectAttr(self.drvCtrl + '.Wavelength', sineNode + '.wavelength')
        cmds.connectAttr(self.drvCtrl + '.Offset', sineNode + '.offset')
        cmds.connectAttr(self.drvCtrl + '.SineRotation', sineHandle + f'.rotate{self.primaryAxis.upper()}')

        # Put Node Group under self.drvCtrl
        cmds.parent(nodeGroup, self.drvCtrl)


        #Hide node group and deformers
        cmds.setAttr(nodeGroup + '.visibility', 0)

def createSquareCurve(name="squareCurve", size=1.0):
    # 定义正方形的顶点坐标
    points = [
        (-size, 0, -size),  # 左下角
        (-size, 0, size),  # 左上角
        (size, 0, size),  # 右上角
        (size, 0, -size),  # 右下角
        (-size, 0, -size)  # 回到左下角，闭合
    ]

    # 创建曲线
    curve = cmds.curve(p=points, d=1, name=name)  # d=1 表示线性曲线，连接点之间为直线
    return curve


def createArrowCurve(name="arrowCurve"):
    """
    Creates a custom controller curve in Maya.

    Args:
        name (str): The name of the controller curve.

    Returns:
        str: The name of the created curve.
    """
    # Define the knot and point data
    knots = [i for i in range(25)]  # Knot values
    points = [(-4.5, 0, 0),
              (-2.5, 0, -2),
              (-2.5, 0, -1.5),
              (-1.5, 0, -1.5),
              (-1.5, 0, -2.5),
              (-2, 0, -2.5),
              (0, 0, -4.5),
              (2, 0, -2.5),
              (1.5, 0, -2.5),
              (1.5, 0, -1.5),
              (2.5, 0, -1.5),
              (2.5, 0, -2),
              (4.5, 0, 0),
              (2.5, 0, 2),
              (2.5, 0, 1.5),
              (1.5, 0, 1.5),
              (1.5, 0, 2.5),
              (2, 0, 2.5),
              (0, 0, 4.5),
              (-2, 0, 2.5),
              (-1.5, 0, 2.5),
              (-1.5, 0, 1.5),
              (-2.5, 0, 1.5),
              (-2.5, 0, 2),
              (-4.5, 0, 0)]

    # Create the curve
    curve = cmds.curve(degree=1, knot=knots, point=points, name=name)
    return curve


# Example Usage
tentacle = Tentacle(
    modelName="tentacle",
    jointCount=18,
    tentacleLength=500,
    isAutoMeasureLength=True,
    primaryAxis='y',
    secondaryAxis='z',
    rollAxis='x',
    drvCtrl="CTRL_M_TentacleDrv_001"
)
tentacle.createRibbonCurve()
tentacle.setUpTentacleFK()
tentacle.tentacleRoll()
tentacle.tentacleRipple()
tentacle.tentacleRibbonDeformer()