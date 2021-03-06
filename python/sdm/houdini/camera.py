"""Utility functions for cameras

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 12/07/17
"""

import sdm.houdini
import hou

import os, logging

logger = logging.getLogger(__name__)

def getCameras():
	"""Gets all cameras in the scene

	Returns:
		list: List of all hou.Node in the current scene that have the type 'cam'
	"""
	return [c for c in hou.node('/').allSubChildren() if c.type().name() == 'cam']

def getSceneViewer():
	"""Gets the scene viewer for the current desktop

	Returns:
	    hou.SceneViewer: The current desktop's scene viewer, or None if there is
	    	no such pane tab created for the current desktop
	"""
	sceneViewer = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.SceneViewer)

	if not sceneViewer:
		logger.warning('Unable to locate pane tab "SceneViewer" in current desktop')
		return None

	return sceneViewer

def getCurrentViewport(viewportType):
	"""Gets the current viewport of the current desktop's scene viewer pane

	Args:
	    viewportType (hou.geometryViewportType): The type of viewport to retrieve from
	    	the current hou.SceneViewer

	Returns:
	    hou.GeometryViewport: The current scene viewer's vewport of the given type, or None
	    	if that type doesn't exist or the scene viewer could not be found
	"""
	sceneViewer = getSceneViewer()

	if not sceneViewer:
		return None

	viewport = [vp for vp in sceneViewer.viewports() if vp.type() == viewportType]

	if not viewport:
		logger.warning('Unable to locate viewport of type {} from scene viewer: {}'.format(viewportType, sceneViewer))
		return None

	return viewport[0]

def flipbook(camera, output=None, frameRange=None):
	"""Outputs a flipbook animation from the given camera

	Args:
	    camera (hou.Node): The camera node to flipbook from
	    output (str, optional): The file path to output the flipbook sequence from. By default,
	    	uses MPlay instead of outputting to a file sequence
	    frameRange (tuple, optional): A tuple representing the start frame, end frame, and frame
	    	increment of the flipbook sequence
	"""
	logger.info('Flipbooking for node: {} at output: {} and frame range: {}'.format(camera, output, frameRange))

	assert camera.type().name() == 'cam', 'Node is not a camera: {}'.format(camera.path())

	sceneViewer = getSceneViewer()

	if not sceneViewer:
		hou.ui.displayMessage('Could not find Scene Viewer pane tab, please create it and try again', title='Flipbook Error', severity=hou.severityType.Error)
		return

	frameStart = int(sceneViewer.flipbookSettings().frameRange()[0])
	frameEnd = int(sceneViewer.flipbookSettings().frameRange()[1])
	frameInc = sceneViewer.flipbookSettings().frameIncrement()

	if frameRange and len(frameRange) >= 2:
		frameStart = frameRange[0]
		frameEnd = frameRange[1]
		frameInc = 1 if len(frameRange) == 2 else frameRange[2]
		logger.debug('Using specified frame range: {}-{} with increment: {}'.format(frameStart, frameEnd, frameInc))
	else:
		logger.debug('Using flipbook settings for frame range: {}-{} with increment: {}'.format(frameStart, frameEnd, frameInc))

	viewport = getCurrentViewport(hou.geometryViewportType.Perspective)

	if not viewport:
		hou.ui.displayMessage('Could not find the "Persp" viewport', title='Flipbook Error', severity=hou.severityType.Error)
		return

	viewportFullName = '{}.{}.world.{}'.format(hou.ui.curDesktop().name(), sceneViewer.name(), viewport.name())

	logger.info('Preparing to flipbook for viewport: {}'.format(viewportFullName))

	hou.setFrame(frameStart)
	viewport.setCamera(camera)

	if output:
		command = "viewwrite -f {} {} -i {} {} '{}'".format(frameStart, frameEnd, frameInc, viewportFullName, output)
	else: # Use Mplay flag instead
		command = "viewwrite -M -f {} {} -i {} {}".format(frameStart, frameEnd, frameInc, viewportFullName)

	logger.debug('Executing HScript: {}'.format(command))
	hou.hscript(command)