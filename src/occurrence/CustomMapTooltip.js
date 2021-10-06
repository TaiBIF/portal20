L.drawLocal = {

	draw: {
		toolbar: {
			actions: {
				title: 'Cancel drawing',
				text: '取消'
			},
			finish: {
				title: 'Finish drawing',
				text: '結束'
			},
			undo: {
				title: 'Delete last point drawn',
				text: 'Delete last point'
			},
			buttons: {
				polyline: 'Draw a polyline',
				polygon: 'Draw a polygon',
				rectangle: '繪製四邊形',
				circle: 'Draw a circle',
				marker: 'Draw a marker',
				circlemarker: 'Draw a circlemarker'
			}
		},
		handlers: {
			circle: {
				tooltip: {
					start: 'Click and drag to draw circle.'
				},
				radius: 'Radius'
			},
			circlemarker: {
				tooltip: {
					start: 'Click map to place circle marker.'
				}
			},
			marker: {
				tooltip: {
					start: 'Click map to place marker.'
				}
			},
			polygon: {
				tooltip: {
					start: 'Click to start drawing shape.',
					cont: 'Click to continue drawing shape.',
					end: 'Click first point to close this shape.'
				}
			},
			polyline: {
				error: '<strong>Error:</strong> shape edges cannot cross!',
				tooltip: {
					start: 'Click to start drawing line.',
					cont: 'Click to continue drawing line.',
					end: 'Click last point to finish line.'
				}
			},
			rectangle: {
				tooltip: {
					start: '點擊並拖曳繪製四邊形',
				}
			},
			simpleshape: {
				tooltip: {
					end: '放開滑鼠結束繪製'
				}
			}
		}
	},
	edit: {
		toolbar: {
			actions: {
				save: {
					title: 'Save changes',
					text: '儲存'
				},
				cancel: {
					title: 'Cancel editing, discards all changes',
					text: '取消'
				},
				clearAll: {
					title: 'Clear all layers',
					text: '清除全部'
				}
			},
			buttons: {
				edit: 'Edit layers',
				editDisabled: 'No layers to edit',
				remove: 'Delete layers',
				removeDisabled: 'No layers to delete'
			}
		},
		handlers: {
			edit: {
				tooltip: {
					text: 'Drag handles or markers to edit features.',
					subtext: 'Click cancel to undo changes.'
				}
			},
			remove: {
				tooltip: {
					text: '點擊欲清除的圖形'
				}
			}
		}
	}
};