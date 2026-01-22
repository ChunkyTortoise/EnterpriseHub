import json
from typing import Dict, Any, List, Optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class PropertyVisualizer:
    """
    Manages metadata and 3D asset paths for the Three.js Digital Twin.
    """
    
    def __init__(self):
        # In production, this would link to an S3/Matterport repository
        self.asset_registry = {
            "123 Maple St": {
                "id": "prop_001",
                "model_url": "https://threejs.org/examples/models/gltf/DamagedHelmet/glTF/DamagedHelmet.gltf", # Placeholder 3D model
                "base_color": "#2D5A7A",
                "stats": {"beds": 4, "baths": 3, "sqft": 2800}
            },
            "456 Oak Ave": {
                "id": "prop_002",
                "model_url": "https://threejs.org/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb",
                "base_color": "#1E88E5",
                "stats": {"beds": 3, "baths": 2, "sqft": 1800}
            }
        }

    def get_digital_twin_metadata(self, address: str) -> Dict[str, Any]:
        """Fetch 3D model and style metadata for a property."""
        return self.asset_registry.get(address, {
            "id": "unknown",
            "model_url": None,
            "base_color": "#8B949E",
            "stats": {}
        })

    def generate_threejs_html(self, address: str) -> str:
        """
        Generates the HTML/JS for a Three.js component with interactive controls.
        """
        meta = self.get_digital_twin_metadata(address)
        stats = meta.get('stats', {})
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background: transparent; overflow: hidden; font-family: 'Inter', sans-serif; }}
        #container {{ width: 100%; height: 350px; cursor: move; border-radius: 12px; }}
        .label {{ position: absolute; top: 10px; left: 10px; color: #00E5FF; font-family: monospace; font-size: 10px; letter-spacing: 1px; text-shadow: 0 0 5px rgba(0,229,255,0.5); }}
        .stats {{ position: absolute; bottom: 10px; right: 10px; color: white; font-size: 10px; background: rgba(0,0,0,0.5); padding: 5px 10px; border-radius: 4px; backdrop-filter: blur(4px); }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div class="label">// DIGITAL_TWIN_RENDER: {address.upper()}</div>
    <div class="stats">{stats.get('beds', 0)} BD | {stats.get('baths', 0)} BA | {stats.get('sqft', 0)} SQFT</div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 350, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, 350);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.getElementById('container').appendChild(renderer.domElement);

        // Group for the house
        const houseGroup = new THREE.Group();
        scene.add(houseGroup);

        // Main body
        const geometry = new THREE.BoxGeometry(1.5, 1, 1.2);
        const material = new THREE.MeshPhongMaterial({{ color: '{meta['base_color']}', flatShading: true }});
        const house = new THREE.Mesh(geometry, material);
        houseGroup.add(house);
        
        // Roof
        const roofGeom = new THREE.CylinderGeometry(0, 1.1, 0.6, 4);
        const roofMat = new THREE.MeshPhongMaterial({{ color: '#1A1A1A' }});
        const roof = new THREE.Mesh(roofGeom, roofMat);
        roof.position.y = 0.8;
        roof.rotation.y = Math.PI / 4;
        houseGroup.add(roof);

        // Door
        const doorGeom = new THREE.PlaneGeometry(0.3, 0.5);
        const doorMat = new THREE.MeshPhongMaterial({{ color: '#3E2723' }});
        const door = new THREE.Mesh(doorGeom, doorMat);
        door.position.set(0, -0.25, 0.601);
        houseGroup.add(door);

        // Windows
        const winGeom = new THREE.PlaneGeometry(0.2, 0.2);
        const winMat = new THREE.MeshPhongMaterial({{ color: '#00E5FF', emissive: '#00E5FF', emissiveIntensity: 0.5 }});
        
        const win1 = new THREE.Mesh(winGeom, winMat);
        win1.position.set(-0.4, 0.1, 0.601);
        houseGroup.add(win1);
        
        const win2 = new THREE.Mesh(winGeom, winMat);
        win2.position.set(0.4, 0.1, 0.601);
        houseGroup.add(win2);

        // Ground reflection / Grid
        const grid = new THREE.GridHelper(10, 20, 0x00E5FF, 0x1A1A1A);
        grid.position.y = -0.5;
        grid.material.opacity = 0.2;
        grid.material.transparent = true;
        scene.add(grid);

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambientLight);
        
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 5, 5);
        scene.add(dirLight);
        
        const pointLight = new THREE.PointLight(0x00E5FF, 1, 10);
        pointLight.position.set(0, 2, 2);
        scene.add(pointLight);

        camera.position.set(3, 2, 3);
        
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 2.0;
        controls.enableZoom = true;
        controls.minDistance = 2;
        controls.maxDistance = 6;

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            const width = window.innerWidth;
            const height = 350;
            renderer.setSize(width, height);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
        }});
    </script>
</body>
</html>
        """
        return html_template
