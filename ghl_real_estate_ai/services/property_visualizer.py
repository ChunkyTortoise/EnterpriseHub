import json
from typing import Any, Dict, List, Optional

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
                "model_url": "https://threejs.org/examples/models/gltf/DamagedHelmet/glTF/DamagedHelmet.gltf",  # Placeholder 3D model
                "base_color": "#2D5A7A",
                "stats": {"beds": 4, "baths": 3, "sqft": 2800},
            },
            "456 Oak Ave": {
                "id": "prop_002",
                "model_url": "https://threejs.org/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb",
                "base_color": "#1E88E5",
                "stats": {"beds": 3, "baths": 2, "sqft": 1800},
            },
        }

    def get_digital_twin_metadata(self, address: str) -> Dict[str, Any]:
        """Fetch 3D model and style metadata for a property."""
        return self.asset_registry.get(
            address, {"id": "unknown", "model_url": None, "base_color": "#8B949E", "stats": {}}
        )

    def generate_threejs_html(self, address: str) -> str:
        """
        Generates the HTML/JS for a Three.js component with interactive controls.
        Supports GLTF loading with fallback to a procedurally generated house.
        """
        meta = self.get_digital_twin_metadata(address)
        stats = meta.get("stats", {})
        model_url = meta.get("model_url")

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; background: transparent; overflow: hidden; font-family: 'Space Grotesk', sans-serif; }}
        #container {{ width: 100%; height: 350px; cursor: move; border-radius: 12px; }}
        .label {{ position: absolute; top: 10px; left: 10px; color: #00E5FF; font-family: monospace; font-size: 10px; letter-spacing: 2px; text-shadow: 0 0 8px rgba(0,229,255,0.6); }}
        .stats {{ position: absolute; bottom: 10px; right: 10px; color: white; font-size: 10px; background: rgba(0,0,0,0.7); padding: 6px 12px; border-radius: 4px; backdrop-filter: blur(8px); border: 1px solid rgba(0,229,255,0.2); }}
        .loading {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00E5FF; font-size: 12px; letter-spacing: 4px; animation: pulse 1.5s infinite; }}
        @keyframes pulse {{ 0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }} }}
    </style>
</head>
<body>
    <div id="loading" class="loading">INITIALIZING_NEURAL_MESH...</div>
    <div id="container"></div>
    <div class="label">// DIGITAL_TWIN_RENDER: {address.upper()}</div>
    <div class="stats">{stats.get("beds", 0)} BD | {stats.get("baths", 0)} BA | {stats.get("sqft", 0)} SQFT</div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    
    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 350, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, 350);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.outputEncoding = THREE.sRGBEncoding;
        document.getElementById('container').appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 1.0;
        controls.enableZoom = true;
        controls.minDistance = 2;
        controls.maxDistance = 8;

        // Lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
        dirLight.position.set(5, 10, 7.5);
        scene.add(dirLight);
        
        const pointLight = new THREE.PointLight(0x00E5FF, 2, 20);
        pointLight.position.set(0, 5, 5);
        scene.add(pointLight);

        // Ground reflection / Grid
        const grid = new THREE.GridHelper(20, 40, 0x00E5FF, 0x1A1A1A);
        grid.position.y = -0.5;
        grid.material.opacity = 0.15;
        grid.material.transparent = true;
        scene.add(grid);

        const loader = new THREE.GLTFLoader();
        const modelUrl = "{model_url if model_url else ""}";
        const loadingEl = document.getElementById('loading');

        function createFallbackHouse() {{
            const houseGroup = new THREE.Group();
            
            // Foundation
            const baseGeom = new THREE.BoxGeometry(2, 1.2, 1.5);
            const baseMat = new THREE.MeshPhongMaterial({{ color: '{meta["base_color"]}', shininess: 100, flatShading: false }});
            const base = new THREE.Mesh(baseGeom, baseMat);
            base.position.y = 0.1;
            houseGroup.add(base);
            
            // Roof (Detailed)
            const roofGeom = new THREE.ConeGeometry(1.6, 1, 4);
            const roofMat = new THREE.MeshPhongMaterial({{ color: '#1A1A1A', shininess: 50 }});
            const roof = new THREE.Mesh(roofGeom, roofMat);
            roof.position.y = 1.2;
            roof.rotation.y = Math.PI / 4;
            houseGroup.add(roof);

            // Door with frame
            const doorGroup = new THREE.Group();
            const doorGeom = new THREE.PlaneGeometry(0.4, 0.7);
            const doorMat = new THREE.MeshPhongMaterial({{ color: '#3E2723' }});
            const door = new THREE.Mesh(doorGeom, doorMat);
            door.position.set(0, -0.15, 0.751);
            doorGroup.add(door);
            houseGroup.add(doorGroup);

            // Glowing Windows
            const winGeom = new THREE.PlaneGeometry(0.3, 0.3);
            const winMat = new THREE.MeshStandardMaterial({{ 
                color: '#00E5FF', 
                emissive: '#00E5FF', 
                emissiveIntensity: 1.5,
                metalness: 0.9,
                roughness: 0.1
            }});
            
            const positions = [
                [-0.6, 0.2, 0.751], [0.6, 0.2, 0.751],
                [-0.6, 0.2, -0.751], [0.6, 0.2, -0.751]
            ];
            
            positions.forEach(pos => {{
                const win = new THREE.Mesh(winGeom, winMat);
                win.position.set(...pos);
                if (pos[2] < 0) win.rotation.y = Math.PI;
                houseGroup.add(win);
            }});

            scene.add(houseGroup);
            loadingEl.style.display = 'none';
        }}

        if (modelUrl && modelUrl.length > 0) {{
            loader.load(modelUrl, 
                (gltf) => {{
                    const model = gltf.scene;
                    // Center model
                    const box = new THREE.Box3().setFromObject(model);
                    const center = box.getCenter(new THREE.Vector3());
                    model.position.sub(center);
                    model.position.y += (box.max.y - box.min.y) / 2;
                    
                    scene.add(model);
                    loadingEl.style.display = 'none';
                    
                    // Adjust camera to fit model
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    camera.position.set(maxDim * 1.5, maxDim, maxDim * 1.5);
                    controls.target.set(0, size.y / 2, 0);
                }},
                (xhr) => {{
                    const percent = Math.round((xhr.loaded / xhr.total) * 100);
                    loadingEl.innerText = `LOADING_MESH: ${{percent}}%`;
                }},
                (error) => {{
                    console.error('Error loading GLTF:', error);
                    createFallbackHouse();
                }}
            );
        }} else {{
            createFallbackHouse();
        }}

        camera.position.set(4, 3, 5);
        controls.target.set(0, 0.5, 0);

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
