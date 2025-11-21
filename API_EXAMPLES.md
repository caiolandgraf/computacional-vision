# 🌐 Exemplos de API Backend

Exemplos de como implementar o backend que receberá os dados do Raspberry Pi.

## 📋 Especificação

### Endpoint

```
POST /api/detections
```

### Request

**Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer {API_KEY}  // Opcional
```

**Form Data:**
```
latitude: -23.550520 (float)
longitude: -46.633308 (float)
confidence: 0.87 (float, 0.0-1.0)
timestamp: 1706234567.89 (float, unix timestamp)
altitude: 750.0 (float, opcional)
detection_type: "pothole" ou "grass" (string)
image: [arquivo JPEG binário]
```

### Response

**Sucesso (200):**
```json
{
  "status": "success",
  "id": "det_12345",
  "message": "Detection saved successfully"
}
```

**Erro (400):**
```json
{
  "status": "error",
  "message": "Invalid coordinates",
  "errors": {
    "latitude": "Must be between -90 and 90"
  }
}
```

**Erro (401):**
```json
{
  "status": "error",
  "message": "Invalid or missing API key"
}
```

**Erro (500):**
```json
{
  "status": "error",
  "message": "Internal server error"
}
```

## 🐍 Python (Flask)

```python
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['API_KEY'] = 'sua-chave-secreta'  # Use env var em produção

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def validate_api_key():
    """Valida API key do header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    
    try:
        scheme, token = auth_header.split(' ')
        if scheme.lower() != 'bearer':
            return False
        return token == app.config['API_KEY']
    except:
        return False

@app.route('/api/detections', methods=['POST'])
def create_detection():
    # Valida API key (opcional)
    if app.config.get('API_KEY') and not validate_api_key():
        return jsonify({
            'status': 'error',
            'message': 'Invalid or missing API key'
        }), 401
    
    try:
        # Extrai dados do form
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        confidence = float(request.form.get('confidence'))
        timestamp = float(request.form.get('timestamp'))
        altitude = request.form.get('altitude')
        detection_type = request.form.get('detection_type', 'pothole')
        
        # Valida coordenadas
        if not (-90 <= latitude <= 90):
            return jsonify({
                'status': 'error',
                'message': 'Invalid latitude',
                'errors': {'latitude': 'Must be between -90 and 90'}
            }), 400
        
        if not (-180 <= longitude <= 180):
            return jsonify({
                'status': 'error',
                'message': 'Invalid longitude',
                'errors': {'longitude': 'Must be between -180 and 180'}
            }), 400
        
        if not (0.0 <= confidence <= 1.0):
            return jsonify({
                'status': 'error',
                'message': 'Invalid confidence',
                'errors': {'confidence': 'Must be between 0.0 and 1.0'}
            }), 400
        
        # Processa imagem
        if 'image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No image provided'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Empty filename'
            }), 400
        
        # Salva imagem
        detection_id = str(uuid.uuid4())
        filename = secure_filename(f"{detection_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Aqui você salvaria no banco de dados
        detection_data = {
            'id': detection_id,
            'latitude': latitude,
            'longitude': longitude,
            'confidence': confidence,
            'timestamp': timestamp,
            'altitude': altitude,
            'detection_type': detection_type,
            'image_path': filepath,
            'created_at': datetime.now().isoformat()
        }
        
        # Exemplo: salvar no banco
        # db.detections.insert_one(detection_data)
        
        print(f"✓ Nova detecção salva: {detection_id}")
        print(f"  Tipo: {detection_type}")
        print(f"  Coordenadas: ({latitude:.6f}, {longitude:.6f})")
        print(f"  Confiança: {confidence:.2f}")
        print(f"  Imagem: {filename}")
        
        return jsonify({
            'status': 'success',
            'id': detection_id,
            'message': 'Detection saved successfully'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid data type: {str(e)}'
        }), 400
    
    except Exception as e:
        print(f"✗ Erro ao processar detecção: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Executar:

```bash
pip install flask
python app.py
```

## 🟢 Node.js (Express)

```javascript
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = 5000;
const API_KEY = 'sua-chave-secreta'; // Use env var em produção

// Configuração do multer para upload
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = 'uploads';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const detectionId = uuidv4();
    const ext = path.extname(file.originalname);
    cb(null, `${detectionId}_${Date.now()}${ext}`);
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 16 * 1024 * 1024 }, // 16MB
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only images are allowed'));
    }
  }
});

// Middleware para validar API key
const validateApiKey = (req, res, next) => {
  const authHeader = req.headers.authorization;
  
  if (!API_KEY) {
    return next(); // API key não configurada, pula validação
  }
  
  if (!authHeader) {
    return res.status(401).json({
      status: 'error',
      message: 'Missing API key'
    });
  }
  
  const [scheme, token] = authHeader.split(' ');
  
  if (scheme.toLowerCase() !== 'bearer' || token !== API_KEY) {
    return res.status(401).json({
      status: 'error',
      message: 'Invalid API key'
    });
  }
  
  next();
};

// Endpoint principal
app.post('/api/detections', validateApiKey, upload.single('image'), (req, res) => {
  try {
    // Extrai dados do form
    const {
      latitude,
      longitude,
      confidence,
      timestamp,
      altitude,
      detection_type = 'pothole'
    } = req.body;
    
    // Valida campos obrigatórios
    if (!latitude || !longitude || !confidence || !timestamp) {
      return res.status(400).json({
        status: 'error',
        message: 'Missing required fields',
        errors: {
          required: ['latitude', 'longitude', 'confidence', 'timestamp']
        }
      });
    }
    
    // Converte para números
    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);
    const conf = parseFloat(confidence);
    const ts = parseFloat(timestamp);
    
    // Valida ranges
    if (lat < -90 || lat > 90) {
      return res.status(400).json({
        status: 'error',
        message: 'Invalid latitude',
        errors: { latitude: 'Must be between -90 and 90' }
      });
    }
    
    if (lon < -180 || lon > 180) {
      return res.status(400).json({
        status: 'error',
        message: 'Invalid longitude',
        errors: { longitude: 'Must be between -180 and 180' }
      });
    }
    
    if (conf < 0 || conf > 1) {
      return res.status(400).json({
        status: 'error',
        message: 'Invalid confidence',
        errors: { confidence: 'Must be between 0.0 and 1.0' }
      });
    }
    
    // Valida imagem
    if (!req.file) {
      return res.status(400).json({
        status: 'error',
        message: 'No image provided'
      });
    }
    
    // Cria objeto de detecção
    const detectionId = path.parse(req.file.filename).name.split('_')[0];
    const detection = {
      id: detectionId,
      latitude: lat,
      longitude: lon,
      confidence: conf,
      timestamp: ts,
      altitude: altitude ? parseFloat(altitude) : null,
      detection_type: detection_type,
      image_path: req.file.path,
      image_filename: req.file.filename,
      created_at: new Date().toISOString()
    };
    
    // Aqui você salvaria no banco de dados
    // await db.detections.insert(detection);
    
    console.log(`✓ Nova detecção salva: ${detectionId}`);
    console.log(`  Tipo: ${detection_type}`);
    console.log(`  Coordenadas: (${lat.toFixed(6)}, ${lon.toFixed(6)})`);
    console.log(`  Confiança: ${conf.toFixed(2)}`);
    console.log(`  Imagem: ${req.file.filename}`);
    
    res.status(200).json({
      status: 'success',
      id: detectionId,
      message: 'Detection saved successfully'
    });
    
  } catch (error) {
    console.error('✗ Erro ao processar detecção:', error);
    res.status(500).json({
      status: 'error',
      message: 'Internal server error'
    });
  }
});

// Tratamento de erros do multer
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    return res.status(400).json({
      status: 'error',
      message: `Upload error: ${error.message}`
    });
  }
  
  res.status(500).json({
    status: 'error',
    message: error.message || 'Internal server error'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 API rodando em http://localhost:${PORT}`);
  console.log(`📍 Endpoint: POST /api/detections`);
});
```

### Executar:

```bash
npm install express multer uuid
node server.js
```

## 🐘 PHP (Laravel)

```php
<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Validator;

class DetectionController extends Controller
{
    /**
     * Cria nova detecção
     *
     * @param Request $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function store(Request $request)
    {
        // Valida API key (middleware)
        // Ver: routes/api.php -> middleware('auth:api')
        
        // Validação
        $validator = Validator::make($request->all(), [
            'latitude' => 'required|numeric|min:-90|max:90',
            'longitude' => 'required|numeric|min:-180|max:180',
            'confidence' => 'required|numeric|min:0|max:1',
            'timestamp' => 'required|numeric',
            'altitude' => 'nullable|numeric',
            'detection_type' => 'required|in:pothole,grass',
            'image' => 'required|image|max:16384', // 16MB
        ]);
        
        if ($validator->fails()) {
            return response()->json([
                'status' => 'error',
                'message' => 'Validation failed',
                'errors' => $validator->errors()
            ], 400);
        }
        
        try {
            // Processa imagem
            $image = $request->file('image');
            $detectionId = (string) Str::uuid();
            $filename = $detectionId . '_' . time() . '.' . $image->extension();
            $path = $image->storeAs('detections', $filename, 'public');
            
            // Salva no banco
            $detection = Detection::create([
                'id' => $detectionId,
                'latitude' => $request->latitude,
                'longitude' => $request->longitude,
                'confidence' => $request->confidence,
                'timestamp' => $request->timestamp,
                'altitude' => $request->altitude,
                'detection_type' => $request->detection_type,
                'image_path' => $path,
            ]);
            
            \Log::info("✓ Nova detecção salva: {$detectionId}", [
                'type' => $request->detection_type,
                'coordinates' => [$request->latitude, $request->longitude],
                'confidence' => $request->confidence,
            ]);
            
            return response()->json([
                'status' => 'success',
                'id' => $detectionId,
                'message' => 'Detection saved successfully'
            ], 200);
            
        } catch (\Exception $e) {
            \Log::error('✗ Erro ao processar detecção: ' . $e->getMessage());
            
            return response()->json([
                'status' => 'error',
                'message' => 'Internal server error'
            ], 500);
        }
    }
}
```

**Migration:**

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateDetectionsTable extends Migration
{
    public function up()
    {
        Schema::create('detections', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->decimal('latitude', 10, 7);
            $table->decimal('longitude', 10, 7);
            $table->decimal('confidence', 3, 2);
            $table->decimal('timestamp', 16, 2);
            $table->decimal('altitude', 8, 2)->nullable();
            $table->enum('detection_type', ['pothole', 'grass']);
            $table->string('image_path');
            $table->timestamps();
            
            $table->index(['latitude', 'longitude']);
            $table->index('detection_type');
            $table->index('timestamp');
        });
    }

    public function down()
    {
        Schema::dropIfExists('detections');
    }
}
```

**Route (routes/api.php):**

```php
Route::post('/detections', [DetectionController::class, 'store'])
    ->middleware('auth:api'); // Opcional
```

## 🗄️ Exemplo de Schema SQL

```sql
-- PostgreSQL
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL,
    timestamp NUMERIC(16, 2) NOT NULL,
    altitude DECIMAL(8, 2),
    detection_type VARCHAR(20) NOT NULL,
    image_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT valid_type CHECK (detection_type IN ('pothole', 'grass'))
);

-- Índices para performance
CREATE INDEX idx_detections_coords ON detections (latitude, longitude);
CREATE INDEX idx_detections_type ON detections (detection_type);
CREATE INDEX idx_detections_timestamp ON detections (timestamp);
CREATE INDEX idx_detections_created ON detections (created_at);

-- MySQL
CREATE TABLE detections (
    id CHAR(36) PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL,
    timestamp DECIMAL(16, 2) NOT NULL,
    altitude DECIMAL(8, 2),
    detection_type ENUM('pothole', 'grass') NOT NULL,
    image_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_coords (latitude, longitude),
    INDEX idx_type (detection_type),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 🧪 Testar API

### cURL

```bash
# Sem autenticação
curl -X POST http://localhost:5000/api/detections \
  -F "latitude=-23.550520" \
  -F "longitude=-46.633308" \
  -F "confidence=0.87" \
  -F "timestamp=1706234567.89" \
  -F "altitude=750.0" \
  -F "detection_type=pothole" \
  -F "image=@foto.jpg"

# Com API key
curl -X POST http://localhost:5000/api/detections \
  -H "Authorization: Bearer sua-chave-secreta" \
  -F "latitude=-23.550520" \
  -F "longitude=-46.633308" \
  -F "confidence=0.87" \
  -F "timestamp=1706234567.89" \
  -F "detection_type=pothole" \
  -F "image=@foto.jpg"
```

### Python (requests)

```python
import requests

url = 'http://localhost:5000/api/detections'
headers = {
    'Authorization': 'Bearer sua-chave-secreta'
}

data = {
    'latitude': -23.550520,
    'longitude': -46.633308,
    'confidence': 0.87,
    'timestamp': 1706234567.89,
    'altitude': 750.0,
    'detection_type': 'pothole'
}

files = {
    'image': open('foto.jpg', 'rb')
}

response = requests.post(url, headers=headers, data=data, files=files)
print(response.status_code)
print(response.json())
```

## 🔐 Segurança

### 1. API Key via Variável de Ambiente

```bash
# .env
API_KEY=sua-chave-super-secreta-aqui
```

```python
# Python
import os
API_KEY = os.getenv('API_KEY')
```

```javascript
// Node.js
require('dotenv').config();
const API_KEY = process.env.API_KEY;
```

### 2. Rate Limiting

```python
# Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/detections', methods=['POST'])
@limiter.limit("10 per minute")
def create_detection():
    # ...
```

### 3. HTTPS Obrigatório

```python
# Flask
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

### 4. Validação de Imagem

```python
from PIL import Image

def validate_image(file_path):
    try:
        img = Image.open(file_path)
        img.verify()
        return True
    except:
        return False
```

## 📊 Monitoramento

### Logs estruturados

```python
import logging
import json

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

@app.route('/api/detections', methods=['POST'])
def create_detection():
    logging.info(json.dumps({
        'event': 'detection_received',
        'detection_type': request.form.get('detection_type'),
        'confidence': request.form.get('confidence'),
        'ip': request.remote_addr
    }))
```

### Métricas

```python
from prometheus_client import Counter, Histogram

detections_total = Counter('detections_total', 'Total detections received')
detections_errors = Counter('detections_errors', 'Total detection errors')
detection_duration = Histogram('detection_duration_seconds', 'Detection processing time')
```

---

**Escolha a stack que melhor se adapta ao seu projeto!**

Todas as implementações seguem a mesma especificação e são compatíveis com o sistema Raspberry Pi.