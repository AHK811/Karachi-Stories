extends Node3D

const PLAYER_SCRIPT = preload("res://scripts/player.gd")

var building_materials: Array[StandardMaterial3D] = []
var road_material: StandardMaterial3D
var sidewalk_material: StandardMaterial3D
var sea_material: StandardMaterial3D

func _ready() -> void:
	_create_materials()
	_create_environment()
	_create_ground()
	_create_roads()
	_create_city_blocks()
	_create_market_details()
	_create_seafront()
	_create_player()
	_create_title_sign()
	_create_hud()

func _create_materials() -> void:
	road_material = _material(Color(0.12, 0.13, 0.14))
	sidewalk_material = _material(Color(0.52, 0.49, 0.43))
	sea_material = _material(Color(0.05, 0.25, 0.34))
	building_materials = [
		_material(Color(0.70, 0.62, 0.49)),
		_material(Color(0.76, 0.72, 0.62)),
		_material(Color(0.63, 0.58, 0.51)),
		_material(Color(0.78, 0.68, 0.56)),
		_material(Color(0.57, 0.61, 0.58)),
		_material(Color(0.72, 0.72, 0.67))
	]

func _material(color: Color) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	return result

func _create_environment() -> void:
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.18, 0.39, 0.58)
	sky_material.sky_horizon_color = Color(0.75, 0.78, 0.74)
	sky_material.ground_bottom_color = Color(0.22, 0.22, 0.20)
	sky_material.ground_horizon_color = Color(0.65, 0.62, 0.54)
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.68, 0.68, 0.65)
	environment.ambient_light_energy = 0.65
	world_environment.environment = environment
	add_child(world_environment)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -32.0, 0.0)
	sun.light_energy = 1.1
	add_child(sun)

func _create_ground() -> void:
	var ground := StaticBody3D.new()
	ground.name = "Ground"
	ground.position.y = -0.55
	add_child(ground)

	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(240.0, 1.0, 240.0)
	mesh.mesh = box
	mesh.material_override = _material(Color(0.60, 0.55, 0.45))
	ground.add_child(mesh)

	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = box.size
	collision.shape = shape
	ground.add_child(collision)

func _create_roads() -> void:
	var road_positions := [-60.0, -30.0, 0.0, 30.0, 60.0]
	for position_value in road_positions:
		_add_road(Vector3(position_value, 0.015, 0.0), Vector3(9.0, 0.08, 150.0))
		_add_road(Vector3(0.0, 0.02, position_value), Vector3(150.0, 0.08, 9.0))

	for position_value in road_positions:
		_add_sidewalk(Vector3(position_value - 5.5, 0.08, 0.0), Vector3(1.5, 0.16, 150.0))
		_add_sidewalk(Vector3(position_value + 5.5, 0.08, 0.0), Vector3(1.5, 0.16, 150.0))
		_add_sidewalk(Vector3(0.0, 0.08, position_value - 5.5), Vector3(150.0, 0.16, 1.5))
		_add_sidewalk(Vector3(0.0, 0.08, position_value + 5.5), Vector3(150.0, 0.16, 1.5))

func _add_road(position_value: Vector3, size_value: Vector3) -> void:
	var road := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size_value
	road.mesh = mesh
	road.material_override = road_material
	road.position = position_value
	add_child(road)

func _add_sidewalk(position_value: Vector3, size_value: Vector3) -> void:
	var sidewalk := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size_value
	sidewalk.mesh = mesh
	sidewalk.material_override = sidewalk_material
	sidewalk.position = position_value
	add_child(sidewalk)

func _create_city_blocks() -> void:
	var centres := [-45.0, -15.0, 15.0, 45.0]
	var index := 0
	for x_value in centres:
		for z_value in centres:
			var commercial := absf(z_value - 15.0) < 0.1 and absf(x_value) < 31.0
			var width := 17.0 if commercial else 15.0 + float(index % 3)
			var depth := 17.0 if commercial else 15.0 + float((index + 1) % 3)
			var height := 6.0 + float((index * 7) % 13)
			if commercial:
				height = 5.5
			_add_building(Vector3(x_value, height * 0.5, z_value), Vector3(width, height, depth), building_materials[index % building_materials.size()], commercial)
			index += 1

func _add_building(position_value: Vector3, size_value: Vector3, material: StandardMaterial3D, commercial: bool) -> void:
	var body := StaticBody3D.new()
	body.position = position_value
	add_child(body)

	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size_value
	mesh_instance.mesh = mesh
	mesh_instance.material_override = material
	body.add_child(mesh_instance)

	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size_value
	collision.shape = shape
	body.add_child(collision)

	if commercial:
		_add_shop_sign(body, size_value)

func _add_shop_sign(parent: Node3D, building_size: Vector3) -> void:
	var sign_mesh := MeshInstance3D.new()
	var sign_box := BoxMesh.new()
	sign_box.size = Vector3(building_size.x * 0.78, 0.8, 0.18)
	sign_mesh.mesh = sign_box
	sign_mesh.position = Vector3(0.0, -1.2, building_size.z * 0.5 + 0.12)
	sign_mesh.material_override = _material(Color(0.65, 0.19, 0.10))
	parent.add_child(sign_mesh)

	var label := Label3D.new()
	label.text = "KARACHI MARKET"
	label.font_size = 36
	label.pixel_size = 0.012
	label.position = sign_mesh.position + Vector3(0.0, 0.0, 0.11)
	label.modulate = Color(1.0, 0.91, 0.70)
	label.billboard = BaseMaterial3D.BILLBOARD_DISABLED
	parent.add_child(label)

func _create_market_details() -> void:
	_add_shop_kiosk(Vector3(-11.0, 0.0, 8.0), "CHAI")
	_add_shop_kiosk(Vector3(11.0, 0.0, 8.0), "BIRYANI")
	_add_parked_rickshaw(Vector3(-7.5, 0.0, 3.0), 0.0)
	_add_parked_rickshaw(Vector3(7.5, 0.0, 3.0), PI)

func _add_shop_kiosk(position_value: Vector3, shop_name: String) -> void:
	var kiosk := Node3D.new()
	kiosk.position = position_value
	add_child(kiosk)

	_add_box(kiosk, Vector3(2.6, 1.8, 1.6), Vector3(0.0, 0.9, 0.0), _material(Color(0.56, 0.34, 0.20)))
	_add_box(kiosk, Vector3(3.0, 0.18, 2.0), Vector3(0.0, 1.95, 0.0), _material(Color(0.63, 0.16, 0.08)))
	var label := Label3D.new()
	label.text = shop_name
	label.font_size = 28
	label.pixel_size = 0.012
	label.position = Vector3(0.0, 2.25, -0.84)
	label.modulate = Color(1.0, 0.94, 0.78)
	kiosk.add_child(label)

func _add_parked_rickshaw(position_value: Vector3, rotation_y: float) -> void:
	var vehicle := Node3D.new()
	vehicle.position = position_value
	vehicle.rotation.y = rotation_y
	add_child(vehicle)
	_add_box(vehicle, Vector3(1.35, 0.9, 2.0), Vector3(0.0, 0.75, 0.0), _material(Color(0.82, 0.62, 0.13)))
	_add_box(vehicle, Vector3(1.15, 0.75, 1.0), Vector3(0.0, 1.55, -0.15), _material(Color(0.12, 0.29, 0.26)))
	for x_value in [-0.62, 0.62]:
		for z_value in [-0.65, 0.65]:
			var wheel := MeshInstance3D.new()
			var cylinder := CylinderMesh.new()
			cylinder.top_radius = 0.28
			cylinder.bottom_radius = 0.28
			cylinder.height = 0.16
			wheel.mesh = cylinder
			wheel.rotation_degrees.z = 90.0
			wheel.position = Vector3(x_value, 0.35, z_value)
			wheel.material_override = _material(Color(0.06, 0.06, 0.06))
			vehicle.add_child(wheel)

func _add_box(parent: Node3D, size_value: Vector3, position_value: Vector3, material: StandardMaterial3D) -> void:
	var instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size_value
	instance.mesh = mesh
	instance.position = position_value
	instance.material_override = material
	parent.add_child(instance)

func _create_seafront() -> void:
	var sea := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3(240.0, 0.2, 35.0)
	sea.mesh = mesh
	sea.position = Vector3(0.0, -0.15, -132.0)
	sea.material_override = sea_material
	add_child(sea)

	var promenade := MeshInstance3D.new()
	var promenade_mesh := BoxMesh.new()
	promenade_mesh.size = Vector3(150.0, 0.15, 4.0)
	promenade.mesh = promenade_mesh
	promenade.position = Vector3(0.0, 0.03, -91.0)
	promenade.material_override = sidewalk_material
	add_child(promenade)

func _create_player() -> void:
	var player := CharacterBody3D.new()
	player.name = "Player"
	player.set_script(PLAYER_SCRIPT)
	player.position = Vector3(0.0, 1.2, 27.0)
	add_child(player)

	var collision := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.42
	capsule.height = 1.8
	collision.shape = capsule
	player.add_child(collision)

	var body_mesh := MeshInstance3D.new()
	var capsule_mesh := CapsuleMesh.new()
	capsule_mesh.radius = 0.42
	capsule_mesh.height = 1.8
	body_mesh.mesh = capsule_mesh
	body_mesh.position.y = 0.0
	body_mesh.material_override = _material(Color(0.12, 0.30, 0.46))
	player.add_child(body_mesh)

func _create_title_sign() -> void:
	var sign := Label3D.new()
	sign.text = "SADDAR DISTRICT  |  KARACHI"
	sign.font_size = 46
	sign.pixel_size = 0.018
	sign.position = Vector3(0.0, 5.0, 17.0)
	sign.modulate = Color(1.0, 0.88, 0.65)
	add_child(sign)

func _create_hud() -> void:
	var layer := CanvasLayer.new()
	var label := Label.new()
	label.text = "KARACHI: STREET STORIES — BLOCKOUT\nWASD: Move   |   Mouse: Look   |   Space: Jump   |   Esc: Unlock cursor"
	label.position = Vector2(22.0, 18.0)
	label.add_theme_font_size_override("font_size", 17)
	label.add_theme_color_override("font_color", Color(1.0, 0.94, 0.82))
	label.add_theme_color_override("font_shadow_color", Color(0.0, 0.0, 0.0, 0.9))
	label.add_theme_constant_override("shadow_offset_x", 2)
	label.add_theme_constant_override("shadow_offset_y", 2)
	layer.add_child(label)
	add_child(layer)
