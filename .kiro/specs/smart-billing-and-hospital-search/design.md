# Design Document: Smart Billing and Hospital Search

## Overview

The Smart Billing and Hospital Search feature consists of two integrated subsystems within the Cerelytic Health platform:

1. **AI Medical Bill Scanner**: Automates extraction of structured data from medical bills using OCR and AI, with anomaly detection and audit logging
2. **SEO-Optimized Hospital Search**: Enables injury-specific hospital discovery with intelligent ranking and public-facing SEO pages

Both subsystems share common infrastructure for authentication, audit logging, and analytics while maintaining clear boundaries for data privacy and access control.

### Technology Stack

- **Backend**: Python (FastAPI) for bill processing services, Node.js (Express) for hospital search API
- **Frontend**: React SPA for authenticated bill scanning interface, Next.js for SEO-optimized public hospital search pages
- **Database**: PostgreSQL for structured data, Redis for caching
- **Storage**: S3-compatible object storage for bill documents
- **Message Queue**: RabbitMQ for asynchronous bill processing
- **External Integrations**: Google Cloud Vision API (OCR), OpenAI API (NLP), hospital directory APIs, Google Maps API (geocoding)

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway / Load Balancer               │
│                     (Authentication, Rate Limiting)              │
└────────────┬────────────────────────────────────┬────────────────┘
             │                                    │
             │                                    │
┌────────────▼─────────────┐         ┌───────────▼──────────────┐
│  Bill Scanner Subsystem  │         │ Hospital Search Subsystem │
│  (Authenticated Users)   │         │  (Public + Authenticated) │
└──────────────────────────┘         └──────────────────────────┘
```

### Bill Scanner Subsystem Components

**1. Bill Ingestion Service**
- Handles file uploads (PDF, PNG, JPEG, HEIC, TIFF)
- Validates file size and format
- Stores original documents in S3 with encryption
- Enqueues processing jobs to message queue
- Returns upload confirmation with job ID

**2. OCR Processing Service**
- Consumes jobs from message queue
- Calls Google Cloud Vision API for text extraction
- Handles multi-page documents
- Calculates confidence scores per field
- Stores raw OCR output for audit trail

**3. Bill Normalization Service**
- Parses OCR text into structured fields
- Uses OpenAI API for intelligent field extraction
- Normalizes dates to ISO 8601
- Normalizes currency to decimal format
- Validates procedure codes against CPT/ICD-10 databases
- Structures line items into consistent schema

**4. Anomaly Detection Service**
- Detects duplicate line items
- Flags out-of-range charges (>3 standard deviations)
- Identifies missing mandatory fields
- Validates totals against sum of line items
- Creates Review_Task records for flagged items

**5. Audit Logging Service**
- Records all extraction events with timestamps
- Logs user edits with before/after values
- Links logs to original documents
- Provides immutable append-only audit trail
- Supports compliance reporting queries

### Hospital Search Subsystem Components

**1. Search API Service**
- Accepts search queries (injury/condition + location)
- Parses free-text injury descriptions using NLP
- Geocodes location strings to coordinates
- Applies filters (insurance, 24x7, language, in-network)
- Returns ranked hospital results
- Logs search events for analytics

**2. Hospital Ranking Engine**
- Calculates Injury_Specialization_Score based on hospital departments
- Weights distance using haversine formula
- Incorporates patient ratings from external APIs
- Factors in cost signals when available
- Prioritizes 24x7 emergency services for ties
- Returns sorted list with ranking metadata

**3. SEO Content Rendering Service**
- Generates human-readable URLs (e.g., /hospitals/acl-tear/chennai)
- Renders server-side pages with Next.js
- Injects schema.org structured data (Hospital, MedicalCondition)
- Creates unique meta tags per injury-location pair
- Generates condition description content blocks
- Implements canonical URLs and sitemaps

**4. Hospital Data Sync Service**
- Fetches hospital data from external directory APIs
- Updates local database with new hospitals and specialties
- Caches external API responses for 24 hours
- Handles rate limits and API failures gracefully
- Maintains data freshness indicators

**5. Search Analytics Service**
- Logs search queries with session IDs
- Tracks hospital result clicks and positions
- Records filter usage patterns
- Aggregates metrics for ranking model tuning
- Anonymizes data by removing PII after 24 hours

### Shared Infrastructure Components

**1. Authentication & Authorization Service**
- Integrates with Cerelytic Auth Service
- Enforces role-based access control (RBAC)
- Validates JWT tokens for API requests
- Manages permissions for PHI access
- Supports anonymous access for public hospital search

**2. Audit Trail Database**
- PostgreSQL with append-only audit tables
- Stores all data access and modification events
- Links to user IDs and session IDs
- Supports HIPAA compliance queries
- Implements retention policies (90-day default)

**3. Analytics & Monitoring**
- Prometheus for metrics collection
- Grafana for dashboards
- Distributed tracing with OpenTelemetry
- Alert manager for error rate thresholds
- Health check endpoints for all services

**4. Cache Layer**
- Redis for search result caching (24-hour TTL)
- Caches geocoding results
- Caches hospital directory data
- Implements cache invalidation on data updates
- Reduces external API costs and latency

## Data Flows

### Bill Processing Flow

```
1. User uploads bill (PDF/image)
   ↓
2. Bill Ingestion Service
   - Validates file format and size
   - Stores in S3 with encryption
   - Creates job record in database
   - Enqueues processing job
   ↓
3. OCR Processing Service (async)
   - Retrieves document from S3
   - Calls Google Cloud Vision API
   - Stores raw OCR text and confidence scores
   - Updates job status
   ↓
4. Bill Normalization Service
   - Parses OCR text with OpenAI API
   - Extracts structured fields
   - Normalizes dates and currency
   - Validates procedure codes
   - Creates Structured_Bill_Data record
   ↓
5. Anomaly Detection Service
   - Checks for duplicates
   - Validates charge ranges
   - Verifies totals
   - Flags missing fields
   - Creates Review_Task records
   ↓
6. Audit Logging Service
   - Records extraction event
   - Links to original document
   - Stores confidence scores
   - Creates immutable log entry
   ↓
7. User reviews extracted data
   - Views structured fields
   - Reviews flagged anomalies
   - Makes manual corrections
   - Marks bill as processed
   ↓
8. Audit Logging Service
   - Records user edits
   - Logs final processing state
   - Completes audit trail
```

### Hospital Search Flow

```
1. User enters search query
   - Injury/condition: "ACL tear"
   - Location: "Chennai"
   - Optional filters: insurance, 24x7, language
   ↓
2. Search API Service
   - Validates input
   - Logs search event with session ID
   ↓
3. NLP Processing
   - Parses injury description
   - Maps to medical specialties (e.g., "ACL tear" → "Orthopedics", "Sports Medicine")
   - Extracts intent and context
   ↓
4. Geocoding
   - Checks Redis cache for location
   - If miss: calls Google Maps Geocoding API
   - Converts "Chennai" to coordinates (13.0827°N, 80.2707°E)
   - Caches result for 24 hours
   ↓
5. Hospital Matching
   - Queries PostgreSQL for hospitals within 50km
   - Filters by specialties matching injury
   - Applies user-specified filters
   - If no results: expands radius to 100km
   ↓
6. Hospital Ranking Engine
   - Calculates Injury_Specialization_Score
   - Computes distance using haversine formula
   - Fetches ratings from cache or external API
   - Retrieves cost signals if available
   - Applies ranking algorithm
   - Sorts results by composite score
   ↓
7. SEO Content Rendering (for public pages)
   - Generates URL: /hospitals/acl-tear/chennai
   - Injects schema.org markup for hospitals
   - Creates meta tags with injury + location
   - Renders condition description content
   - Returns server-side rendered HTML
   ↓
8. Search Analytics Service
   - Logs query, filters, result count
   - Records user clicks on results
   - Tracks session behavior
   - Anonymizes PII after 24 hours
```

## Components and Interfaces

### Bill Ingestion Service

**Responsibilities:**
- Accept file uploads via multipart/form-data
- Validate file format, size, and content type
- Store documents in S3 with server-side encryption
- Generate unique document IDs
- Enqueue processing jobs to RabbitMQ

**API Endpoints:**

```
POST /api/v1/bills/upload
Request:
  - Content-Type: multipart/form-data
  - Body: file (PDF/image), userId, metadata
Response:
  - 201 Created: { billId, jobId, status: "queued" }
  - 400 Bad Request: { error: "Invalid file format" }
  - 413 Payload Too Large: { error: "File exceeds 25MB limit" }

GET /api/v1/bills/{billId}/status
Response:
  - 200 OK: { billId, status, progress, extractedData }
```

**Internal Interfaces:**

```python
class BillIngestionService:
    def upload_bill(self, file: UploadFile, user_id: str, metadata: dict) -> BillUploadResult:
        """
        Validates and stores uploaded bill, enqueues processing job
        Returns: BillUploadResult with billId and jobId
        """
        pass
    
    def get_bill_status(self, bill_id: str, user_id: str) -> BillStatus:
        """
        Retrieves current processing status and extracted data
        Enforces access control based on user_id
        """
        pass
```

### OCR Processing Service

**Responsibilities:**
- Consume processing jobs from RabbitMQ
- Call Google Cloud Vision API for text extraction
- Handle multi-page documents
- Calculate field-level confidence scores
- Store raw OCR output for audit

**Internal Interfaces:**

```python
class OCRProcessingService:
    def process_bill(self, job: ProcessingJob) -> OCRResult:
        """
        Extracts text from bill document using OCR
        Returns: OCRResult with text, confidence scores, and page metadata
        """
        pass
    
    def retry_with_preprocessing(self, job: ProcessingJob) -> OCRResult:
        """
        Applies image preprocessing (deskew, contrast) and retries OCR
        Used when initial confidence is low
        """
        pass
```

### Bill Normalization Service

**Responsibilities:**
- Parse OCR text into structured fields
- Use LLM for intelligent field extraction
- Normalize dates, currency, and codes
- Validate against medical coding databases
- Create Structured_Bill_Data records

**Internal Interfaces:**

```python
class BillNormalizationService:
    def normalize_bill(self, ocr_result: OCRResult) -> StructuredBillData:
        """
        Converts raw OCR text to structured bill data
        Returns: StructuredBillData with normalized fields
        """
        pass
    
    def validate_codes(self, bill_data: StructuredBillData) -> ValidationResult:
        """
        Validates procedure codes against CPT/ICD-10 databases
        Returns: ValidationResult with valid/invalid codes
        """
        pass
```

### Anomaly Detection Service

**Responsibilities:**
- Detect duplicate line items
- Flag out-of-range charges
- Identify missing mandatory fields
- Validate totals against line item sums
- Create Review_Task records

**Internal Interfaces:**

```python
class AnomalyDetectionService:
    def detect_anomalies(self, bill_data: StructuredBillData) -> List[Anomaly]:
        """
        Analyzes bill data for potential errors
        Returns: List of detected anomalies with severity and description
        """
        pass
    
    def calculate_charge_statistics(self, procedure_code: str) -> ChargeStatistics:
        """
        Retrieves historical charge statistics for a procedure
        Used to detect out-of-range prices
        """
        pass
```

### Search API Service

**Responsibilities:**
- Accept and validate search queries
- Parse injury descriptions with NLP
- Geocode location strings
- Apply filters and return ranked results
- Log search events

**API Endpoints:**

```
GET /api/v1/hospitals/search
Query Parameters:
  - injury: string (e.g., "ACL tear")
  - location: string (e.g., "Chennai" or "13.0827,80.2707")
  - insurance: string (optional)
  - emergency24x7: boolean (optional)
  - language: string (optional)
  - inNetwork: boolean (optional)
Response:
  - 200 OK: { results: [Hospital], totalCount, searchId }
  - 400 Bad Request: { error: "Invalid query parameters" }

GET /hospitals/{injury-slug}/{location-slug}
Path Parameters:
  - injury-slug: string (e.g., "acl-tear")
  - location-slug: string (e.g., "chennai")
Response:
  - 200 OK: Server-side rendered HTML with SEO markup
  - 404 Not Found: { error: "No hospitals found" }
```

**Internal Interfaces:**

```typescript
interface SearchAPIService {
  searchHospitals(query: SearchQuery): Promise<SearchResult>;
  parseInjuryDescription(injury: string): Promise<MedicalSpecialty[]>;
  geocodeLocation(location: string): Promise<Coordinates>;
  applyFilters(hospitals: Hospital[], filters: SearchFilters): Hospital[];
}
```

### Hospital Ranking Engine

**Responsibilities:**
- Calculate specialization scores
- Compute distances using haversine formula
- Fetch and incorporate ratings
- Apply ranking algorithm
- Return sorted results with metadata

**Internal Interfaces:**

```typescript
interface HospitalRankingEngine {
  rankHospitals(
    hospitals: Hospital[],
    userLocation: Coordinates,
    requiredSpecialties: MedicalSpecialty[]
  ): Promise<RankedHospital[]>;
  
  calculateSpecializationScore(
    hospital: Hospital,
    requiredSpecialties: MedicalSpecialty[]
  ): number;
  
  calculateDistance(
    point1: Coordinates,
    point2: Coordinates
  ): number;
}
```

### SEO Content Rendering Service

**Responsibilities:**
- Generate SEO-friendly URLs
- Render server-side pages with Next.js
- Inject structured data markup
- Create unique meta tags
- Generate condition descriptions

**Internal Interfaces:**

```typescript
interface SEOContentRenderer {
  renderHospitalSearchPage(
    injury: string,
    location: string,
    results: RankedHospital[]
  ): Promise<string>; // Returns HTML
  
  generateStructuredData(hospitals: Hospital[]): SchemaOrgMarkup;
  generateMetaTags(injury: string, location: string): MetaTags;
  generateConditionDescription(injury: string): string;
}
```

## Data Models

### Bill

```typescript
interface Bill {
  billId: string;              // UUID
  userId: string;              // User who uploaded
  documentUrl: string;         // S3 URL
  documentHash: string;        // SHA-256 hash
  uploadedAt: Date;
  status: BillStatus;          // queued, processing, completed, failed
  extractedData?: StructuredBillData;
  anomalies: Anomaly[];
  auditLog: AuditEntry[];
}

enum BillStatus {
  QUEUED = "queued",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  REVIEW_REQUIRED = "review_required"
}
```

### StructuredBillData

```typescript
interface StructuredBillData {
  patient: {
    name: string;
    dateOfBirth: string;        // ISO 8601
    patientId: string;
    confidenceScore: number;    // 0-1
  };
  provider: {
    name: string;
    address: string;
    taxId: string;
    confidenceScore: number;
  };
  datesOfService: {
    startDate: string;           // ISO 8601
    endDate: string;
    confidenceScore: number;
  };
  lineItems: BillLineItem[];
  totals: {
    totalCharges: number;        // Decimal
    amountPaid: number;
    amountDue: number;
    currency: string;            // ISO 4217 (e.g., "USD", "INR")
  };
  payer?: {
    insuranceCompany: string;
    policyNumber: string;
    confidenceScore: number;
  };
  diagnosisCodes?: string[];     // ICD-10/ICD-9
}
```

### BillLineItem

```typescript
interface BillLineItem {
  lineNumber: number;
  procedureCode: string;         // CPT code
  description: string;
  quantity: number;
  unitPrice: number;
  totalCharge: number;
  dateOfService: string;         // ISO 8601
  confidenceScore: number;
}
```

### Anomaly

```typescript
interface Anomaly {
  anomalyId: string;
  billId: string;
  type: AnomalyType;
  severity: Severity;
  description: string;
  affectedFields: string[];
  suggestedAction: string;
  detectedAt: Date;
  resolvedAt?: Date;
  resolvedBy?: string;
}

enum AnomalyType {
  DUPLICATE_LINE_ITEM = "duplicate_line_item",
  OUT_OF_RANGE_CHARGE = "out_of_range_charge",
  MISSING_FIELD = "missing_field",
  TOTAL_MISMATCH = "total_mismatch",
  INVALID_CODE = "invalid_code"
}

enum Severity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical"
}
```

### Hospital

```typescript
interface Hospital {
  hospitalId: string;
  name: string;
  address: string;
  coordinates: Coordinates;
  specialties: MedicalSpecialty[];
  certifications: string[];
  ratings: {
    averageRating: number;       // 0-5
    reviewCount: number;
    source: string;              // e.g., "Google", "Healthgrades"
  };
  emergency24x7: boolean;
  insuranceAccepted: string[];
  languagesSupported: string[];
  costSignals?: {
    averageProcedureCost: number;
    currency: string;
  };
  lastUpdated: Date;
}

interface Coordinates {
  latitude: number;
  longitude: number;
}
```

### MedicalSpecialty

```typescript
interface MedicalSpecialty {
  specialtyId: string;
  name: string;                  // e.g., "Orthopedics"
  subSpecialties: string[];      // e.g., ["Sports Medicine", "Joint Replacement"]
  relatedConditions: string[];   // e.g., ["ACL tear", "Meniscus injury"]
}
```

### SearchEvent

```typescript
interface SearchEvent {
  searchId: string;
  sessionId: string;
  timestamp: Date;
  query: {
    injury: string;
    location: string;
    filters: SearchFilters;
  };
  results: {
    hospitalIds: string[];
    resultCount: number;
  };
  userActions: {
    clickedHospitalId?: string;
    clickPosition?: number;
    viewDuration?: number;       // seconds
  };
  anonymizedAt?: Date;           // When PII was removed
}

interface SearchFilters {
  insurance?: string;
  emergency24x7?: boolean;
  language?: string;
  inNetwork?: boolean;
}
```

### AuditEntry

```typescript
interface AuditEntry {
  auditId: string;
  billId: string;
  userId: string;
  action: AuditAction;
  timestamp: Date;
  details: {
    fieldName?: string;
    oldValue?: any;
    newValue?: any;
    confidenceScore?: number;
  };
  ipAddress?: string;            // Hashed for privacy
  userAgent?: string;
}

enum AuditAction {
  BILL_UPLOADED = "bill_uploaded",
  OCR_COMPLETED = "ocr_completed",
  DATA_EXTRACTED = "data_extracted",
  FIELD_EDITED = "field_edited",
  ANOMALY_DETECTED = "anomaly_detected",
  ANOMALY_RESOLVED = "anomaly_resolved",
  BILL_PROCESSED = "bill_processed",
  DATA_ACCESSED = "data_accessed"
}
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated:
- Multiple extraction completeness properties (2.1-2.8) can be combined into comprehensive extraction properties
- Filter properties (9.1-9.4) follow the same pattern and can be generalized
- Logging properties (11.1-11.4) share common structure
- Normalization properties (3.1-3.2) are related transformations

The following properties represent the unique, non-redundant correctness guarantees for this system.

### Bill Scanner Properties

**Property 1: File Upload Validation**
*For any* uploaded file, if the file size is under 25MB and the format is one of PDF, PNG, JPEG, HEIC, or TIFF, then the Bill_Scanner should accept the upload; otherwise it should reject with an appropriate error message.
**Validates: Requirements 1.1, 1.2**

**Property 2: Multi-Page Processing Order**
*For any* multi-page document, the Bill_Scanner should process all pages and the extracted data should maintain the original page order.
**Validates: Requirements 1.3**

**Property 3: Patient Data Extraction Completeness**
*For any* bill containing patient information, the Bill_Scanner should extract all three fields: patient name, date of birth, and patient identifier, each with a confidence score.
**Validates: Requirements 2.1**

**Property 4: Provider Data Extraction Completeness**
*For any* bill containing provider information, the Bill_Scanner should extract all three fields: provider name, address, and tax identification number.
**Validates: Requirements 2.2**

**Property 5: Line Item Extraction Completeness**
*For any* bill line item, the Bill_Scanner should extract date of service, procedure code, description, quantity, unit price, and total charge.
**Validates: Requirements 2.3, 2.4, 2.6**

**Property 6: Conditional Field Extraction**
*For any* bill, if diagnosis codes or payer information are present in the document, then the Bill_Scanner should extract them; if absent, the corresponding fields should be null or empty.
**Validates: Requirements 2.5, 2.8**

**Property 7: Totals Extraction Completeness**
*For any* bill, the Bill_Scanner should extract all three total fields: total amount, amount paid, and amount due.
**Validates: Requirements 2.7**

**Property 8: Currency Normalization**
*For any* extracted currency amount, the Bill_Scanner should normalize it to a standard decimal format with consistent precision.
**Validates: Requirements 3.1**

**Property 9: Date Normalization**
*For any* extracted date, the Bill_Scanner should normalize it to ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ).
**Validates: Requirements 3.2**

**Property 10: Procedure Code Validation**
*For any* extracted procedure code, the Bill_Scanner should validate it against standard medical coding systems (CPT) and flag invalid codes.
**Validates: Requirements 3.3**

**Property 11: Schema Conformance**
*For any* bill processing result, the output should conform to the Structured_Bill_Data schema with all required fields present and correctly typed.
**Validates: Requirements 3.4, 3.5**

**Property 12: Duplicate Detection**
*For any* bill with duplicate line items (same procedure code, date, and amount), the Bill_Scanner should create an Anomaly flagged as a Review_Task.
**Validates: Requirements 4.1**

**Property 13: Outlier Charge Detection**
*For any* line item charge that is more than 3 standard deviations from the historical mean for that procedure code, the Bill_Scanner should create an Anomaly.
**Validates: Requirements 4.2**

**Property 14: Missing Field Detection**
*For any* bill with missing mandatory fields (patient name, provider name, or total amount), the Bill_Scanner should create an Anomaly listing the missing fields.
**Validates: Requirements 4.3**

**Property 15: Total Validation**
*For any* bill where the extracted total does not equal the sum of line item charges (within 0.01 tolerance), the Bill_Scanner should create an Anomaly with the discrepancy amount.
**Validates: Requirements 4.4**

**Property 16: Anomaly Presentation**
*For any* created Anomaly, it should include a description, severity level, affected fields, and suggested action for UI display.
**Validates: Requirements 4.5**

**Property 17: Upload Audit Logging**
*For any* bill upload, the Bill_Scanner should create an Extraction_Log entry containing timestamp, user ID, and document hash.
**Validates: Requirements 5.1**

**Property 18: Extraction Audit Completeness**
*For any* completed extraction, the Extraction_Log should contain all extracted field names, values, and confidence scores.
**Validates: Requirements 5.2**

**Property 19: Edit Audit Trail**
*For any* user edit to extracted data, the Bill_Scanner should append an audit entry with old value, new value, user ID, and timestamp.
**Validates: Requirements 5.3**

**Property 20: Processing Completion Logging**
*For any* bill marked as processed, the Extraction_Log should contain the final state and processing timestamp.
**Validates: Requirements 5.4**

**Property 21: Audit-Document Linkage**
*For any* Extraction_Log entry, it should contain a valid reference to the original uploaded document that can be used for retrieval.
**Validates: Requirements 5.5**

**Property 22: Low Confidence Handling**
*For any* bill where overall OCR confidence is below 60%, the Bill_Scanner should mark it as unreadable and notify the user.
**Validates: Requirements 6.1**

**Property 23: Partial Extraction Handling**
*For any* bill with partial extraction success (some fields extracted, others missing), the Bill_Scanner should present extracted fields for review and allow manual completion of missing fields.
**Validates: Requirements 6.3**

**Property 24: OCR Failure Logging**
*For any* complete OCR failure, the Bill_Scanner should log the failure with error details and suggest document quality improvements.
**Validates: Requirements 6.4**

**Property 25: Error Recovery**
*For any* processing error, the Bill_Scanner should preserve the uploaded document and allow retry without requiring re-upload.
**Validates: Requirements 6.5**

**Property 26: Access Control Enforcement**
*For any* attempt to access bill data, the Bill_Scanner should verify the user has appropriate role-based permissions before returning data.
**Validates: Requirements 12.3**

**Property 27: Data Masking**
*For any* display of patient data, sensitive fields (SSN, full DOB) should be masked by default unless explicitly revealed by an authorized user.
**Validates: Requirements 12.4**

**Property 28: Retry with Exponential Backoff**
*For any* OCR service failure, the Bill_Scanner should retry up to 3 times with exponential backoff (delays of 1s, 2s, 4s).
**Validates: Requirements 15.1**

**Property 29: Document Preservation on Failure**
*For any* failed processing job, the Bill_Scanner should preserve the uploaded document in storage and maintain its accessibility for retry.
**Validates: Requirements 15.3**

**Property 30: Offline Job Queuing**
*For any* extraction job submitted when network connectivity is lost, the Bill_Scanner should queue the job and process it when connectivity is restored.
**Validates: Requirements 15.4**

**Property 31: Rate Limit Handling**
*For any* OCR API rate limit error, the Bill_Scanner should handle it gracefully by queuing the job and retrying after the rate limit window.
**Validates: Requirements 16.3**

**Property 32: API Response Caching**
*For any* external API response (geocoding, hospital data), the Hospital_Search_Engine should cache it for 24 hours and serve from cache within that TTL.
**Validates: Requirements 16.5**

**Property 33: Processing Metrics Emission**
*For any* completed bill processing, the Bill_Scanner should emit metrics including processing time, extraction accuracy percentage, and anomaly count.
**Validates: Requirements 17.1**

**Property 34: Alert Threshold Triggering**
*For any* 5-minute window where error rate exceeds 5%, the Bill_Scanner should trigger an alert to the operations team.
**Validates: Requirements 17.3**

**Property 35: Dependency Failure Alerting**
*For any* external API dependency failure, the Hospital_Search_Engine should emit an alert containing the service name and error details.
**Validates: Requirements 17.4**

### Hospital Search Properties

**Property 36: Injury Description Mapping**
*For any* free-text injury description, the Hospital_Search_Engine should map it to one or more relevant medical specialties.
**Validates: Requirements 7.2**

**Property 37: Location Format Flexibility**
*For any* location input (address, city, postal code, or coordinates), the Hospital_Search_Engine should accept it and convert it to coordinates for distance calculation.
**Validates: Requirements 7.3**

**Property 38: Search Result Completeness**
*For any* hospital in search results, the result should include hospital name, address, distance, specialization match score, and ratings.
**Validates: Requirements 7.4**

**Property 39: Search Radius Expansion**
*For any* search with no hospitals within 50km, the Hospital_Search_Engine should expand the search radius to 100km and inform the user of the expansion.
**Validates: Requirements 7.5**

**Property 40: Specialization Score Calculation**
*For any* hospital and required specialty set, the Hospital_Search_Engine should calculate an Injury_Specialization_Score based on matching departments and certifications.
**Validates: Requirements 8.1**

**Property 41: Distance-Based Ranking**
*For any* two hospitals with equal specialization scores and ratings, the closer hospital should rank higher in results.
**Validates: Requirements 8.2**

**Property 42: Rating Incorporation**
*For any* hospital ranking, patient ratings and review scores should be factored into the composite ranking score.
**Validates: Requirements 8.3**

**Property 43: Cost Signal Ranking**
*For any* hospital with available cost signals, the average procedure cost should be factored into the ranking (lower cost increases rank when other factors are equal).
**Validates: Requirements 8.4**

**Property 44: Emergency Service Tiebreaker**
*For any* two hospitals with similar composite scores (within 5% difference), the hospital with 24x7 emergency services should rank higher.
**Validates: Requirements 8.5**

**Property 45: Insurance Filter Application**
*For any* search with an insurance filter applied, all returned hospitals should accept that insurance.
**Validates: Requirements 9.1**

**Property 46: Emergency Filter Application**
*For any* search with a 24x7 emergency filter applied, all returned hospitals should have round-the-clock emergency departments.
**Validates: Requirements 9.2**

**Property 47: Language Filter Application**
*For any* search with a language filter applied, all returned hospitals should have staff speaking the specified language.
**Validates: Requirements 9.3**

**Property 48: Network Filter Application**
*For any* search with an in-network filter applied, all returned hospitals should be in the user's insurance network.
**Validates: Requirements 9.4**

**Property 49: SEO URL Generation**
*For any* search result page, the URL should be human-readable and contain slugified versions of the injury and location (e.g., /hospitals/acl-tear/chennai).
**Validates: Requirements 10.1**

**Property 50: Structured Data Inclusion**
*For any* rendered landing page, the HTML should include schema.org structured data for Hospital and MedicalCondition entities.
**Validates: Requirements 10.2**

**Property 51: Meta Tag Generation**
*For any* landing page, the HTML should include meta title and description tags containing the injury and location terms.
**Validates: Requirements 10.3**

**Property 52: Content Block Generation**
*For any* landing page, the HTML should include content blocks describing the condition, treatments, and hospital specialties.
**Validates: Requirements 10.4**

**Property 53: Content Uniqueness**
*For any* two different injury-location combinations, the generated landing page content should be unique (not duplicated).
**Validates: Requirements 10.5**

**Property 54: Search Event Logging**
*For any* search performed, the Hospital_Search_Engine should log an event containing query text, location, timestamp, and session ID.
**Validates: Requirements 11.1**

**Property 55: Click Event Logging**
*For any* hospital result click, the Hospital_Search_Engine should log the hospital ID, rank position, and timestamp.
**Validates: Requirements 11.2**

**Property 56: Filter Event Logging**
*For any* filter application, the Hospital_Search_Engine should log the filter types and values.
**Validates: Requirements 11.3**

**Property 57: View Event Logging**
*For any* hospital detail view, the Hospital_Search_Engine should log the view with duration and any actions taken.
**Validates: Requirements 11.4**

**Property 58: PII Removal in Analytics**
*For any* aggregated search analytics data, personally identifiable information (IP addresses, device IDs) should be removed.
**Validates: Requirements 11.5**

**Property 59: IP Address Retention**
*For any* search log entry, IP addresses and device identifiers should be purged after 24 hours.
**Validates: Requirements 13.2**

**Property 60: Session Expiration**
*For any* user session, it should expire after 30 minutes of inactivity.
**Validates: Requirements 13.4**

**Property 61: Session Cleanup**
*For any* cleared user session, all associated search history should be deleted.
**Validates: Requirements 13.5**

**Property 62: Cached Fallback**
*For any* search when external hospital data sources are unavailable, the Hospital_Search_Engine should serve cached results and display a staleness warning.
**Validates: Requirements 15.2**

**Property 63: Geocoding Integration**
*For any* address string, the Hospital_Search_Engine should use the geocoding API to convert it to valid coordinates (latitude, longitude).
**Validates: Requirements 16.2**

**Property 64: Search Metrics Emission**
*For any* search performed, the Hospital_Search_Engine should emit metrics including query latency, result count, and applied filters.
**Validates: Requirements 17.2**

## Error Handling

### Bill Scanner Error Scenarios

**1. File Upload Errors**
- **Oversized files (>25MB)**: Return 413 Payload Too Large with clear message
- **Unsupported formats**: Return 400 Bad Request listing supported formats
- **Corrupted files**: Return 400 Bad Request suggesting file re-export
- **Storage failures**: Return 503 Service Unavailable, preserve upload for retry

**2. OCR Processing Errors**
- **Low confidence (<60%)**: Mark as unreadable, offer manual entry UI
- **Complete OCR failure**: Log error, suggest image quality improvements, allow retry
- **Timeout**: Retry with exponential backoff (3 attempts), then mark as failed
- **Rate limit exceeded**: Queue job, retry after rate limit window

**3. Extraction Errors**
- **No structured data found**: Provide manual entry form with original document visible
- **Partial extraction**: Show extracted fields, highlight missing fields for manual entry
- **Invalid procedure codes**: Flag as anomaly, allow manual correction
- **Schema validation failure**: Log error, preserve raw data, notify operations team

**4. Anomaly Detection Errors**
- **Missing historical data for outlier detection**: Skip outlier check, log warning
- **Database unavailable**: Queue anomaly detection, process when available
- **Calculation errors**: Log error, continue processing without anomaly detection

**5. Audit Logging Errors**
- **Audit database unavailable**: Queue audit entries, write when available
- **Disk full**: Alert operations team, block new uploads until resolved
- **Log corruption**: Alert operations team, maintain redundant logs

### Hospital Search Error Scenarios

**1. Search Query Errors**
- **Empty query**: Return 400 Bad Request with validation message
- **Invalid location**: Return 400 Bad Request suggesting valid formats
- **Malformed filters**: Return 400 Bad Request with filter schema

**2. NLP Processing Errors**
- **Unrecognized injury term**: Return results for general medicine, suggest alternatives
- **Ambiguous injury**: Return results for multiple specialties, ask user to clarify
- **API timeout**: Use cached mappings if available, otherwise return generic results

**3. Geocoding Errors**
- **Location not found**: Return 404 with suggestion to try nearby city
- **Geocoding API unavailable**: Use cached coordinates if available, otherwise return error
- **Rate limit exceeded**: Serve from cache, queue geocoding for background processing

**4. Hospital Data Errors**
- **External API unavailable**: Serve cached results with staleness warning
- **Incomplete hospital data**: Return results with available fields, mark missing data
- **Stale cache**: Serve stale data, trigger background refresh, display last-updated timestamp

**5. Ranking Errors**
- **Missing rating data**: Rank without ratings, note unavailability
- **Distance calculation failure**: Log error, exclude hospital from results
- **Specialization score calculation error**: Use default score, log error

**6. SEO Rendering Errors**
- **Template rendering failure**: Return 500 Internal Server Error, log error
- **Structured data generation error**: Render page without schema.org markup, log warning
- **Content generation timeout**: Serve cached page if available, otherwise return basic results

### Resilience Patterns

**1. Retry with Exponential Backoff**
- Applied to: OCR API calls, external hospital directory queries, geocoding requests
- Configuration: 3 retries with delays of 1s, 2s, 4s
- Circuit breaker: After 10 consecutive failures, open circuit for 60 seconds

**2. Graceful Degradation**
- Hospital search serves cached results when external APIs fail
- Bill scanner offers manual entry when OCR fails
- Ranking continues without ratings if rating API is unavailable

**3. Asynchronous Processing**
- Bill processing jobs queued in RabbitMQ for async execution
- Failed jobs preserved for manual retry
- Job status tracked in database for user visibility

**4. Idempotency**
- Bill uploads use unique document hashes to prevent duplicates
- Audit log entries use unique IDs to prevent duplicate logging
- Search result caching uses query hash as key

**5. Health Checks**
- All services expose /health endpoints
- Health checks verify: database connectivity, external API availability, storage access
- Load balancer removes unhealthy instances from rotation

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests**: Validate specific examples, edge cases, and error conditions
- Focus on concrete scenarios with known inputs and expected outputs
- Test integration points between components
- Verify error handling for specific failure modes
- Test UI components and user interactions

**Property Tests**: Verify universal properties across all inputs
- Generate random inputs to test properties at scale
- Validate invariants that should hold for all valid data
- Test round-trip properties (e.g., serialize/deserialize)
- Verify metamorphic properties (e.g., filtering reduces result count)

### Property-Based Testing Configuration

**Testing Library**: Use `hypothesis` for Python services, `fast-check` for TypeScript/Node.js services

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: smart-billing-and-hospital-search, Property {number}: {property_text}`

**Example Property Test Structure**:

```python
from hypothesis import given, strategies as st

@given(
    file_size=st.integers(min_value=0, max_value=50_000_000),
    file_format=st.sampled_from(['pdf', 'png', 'jpg', 'heic', 'tiff', 'doc', 'txt'])
)
def test_file_upload_validation(file_size, file_format):
    """
    Feature: smart-billing-and-hospital-search
    Property 1: File Upload Validation
    
    For any uploaded file, if the file size is under 25MB and the format
    is one of PDF, PNG, JPEG, HEIC, or TIFF, then the Bill_Scanner should
    accept the upload; otherwise it should reject with an appropriate error.
    
    Validates: Requirements 1.1, 1.2
    """
    result = bill_scanner.validate_upload(file_size, file_format)
    
    valid_formats = ['pdf', 'png', 'jpg', 'jpeg', 'heic', 'tiff']
    max_size = 25 * 1024 * 1024  # 25MB
    
    if file_size <= max_size and file_format.lower() in valid_formats:
        assert result.is_valid
    else:
        assert not result.is_valid
        assert result.error_message is not None
```

### Unit Testing Strategy

**Bill Scanner Unit Tests**:
- Test specific bill formats (CMS-1500, UB-04)
- Test edge cases: handwritten notes, multi-language bills, redacted sections
- Test error messages for specific failure scenarios
- Test UI components for manual entry and anomaly review

**Hospital Search Unit Tests**:
- Test specific injury-location combinations
- Test filter combinations
- Test SEO markup generation for known inputs
- Test UI components for search and results display

**Integration Tests**:
- Test end-to-end bill processing flow
- Test end-to-end search flow
- Test authentication and authorization
- Test audit logging across components

### Test Coverage Goals

- Line coverage: >80% for all services
- Branch coverage: >75% for business logic
- Property test coverage: 100% of correctness properties
- Integration test coverage: All critical user flows

## Security and Compliance Design

### Data Encryption

**At Rest**:
- All uploaded bill documents encrypted with AES-256 in S3
- Database encryption enabled for PostgreSQL (TDE)
- Encryption keys managed via AWS KMS or similar
- Key rotation every 90 days

**In Transit**:
- TLS 1.3 for all API communications
- Certificate pinning for mobile clients
- Mutual TLS for service-to-service communication
- No sensitive data in URL parameters or logs

### Access Control

**Role-Based Access Control (RBAC)**:
- **Patient Role**: View own bills, search hospitals anonymously
- **Billing Staff Role**: Upload bills, view/edit extracted data, resolve anomalies
- **Admin Role**: Access all bills, manage users, view audit logs
- **System Role**: Internal service-to-service communication

**Permission Enforcement**:
- JWT tokens with role claims
- Token expiration: 1 hour for users, 5 minutes for services
- Refresh tokens: 30 days for users
- All API endpoints validate permissions before processing

### Audit Trail

**Audit Log Contents**:
- User ID and role
- Action performed (upload, view, edit, delete)
- Timestamp (UTC)
- Resource ID (bill ID, hospital ID)
- Before/after values for edits
- IP address (hashed)
- User agent

**Audit Log Storage**:
- Append-only PostgreSQL tables
- Separate database for audit logs
- Retention: 7 years for HIPAA compliance
- Immutable: No updates or deletes allowed
- Backed up daily to separate storage

### Privacy Controls

**Data Minimization**:
- Hospital search requires no PHI
- Anonymous sessions for public search
- IP addresses purged after 24 hours
- Session data purged after 30 days

**Data Masking**:
- SSN masked: XXX-XX-1234
- DOB masked: XX/XX/1990
- Full data visible only to authorized users
- Masking applied at API layer

**Right to Deletion**:
- Users can request bill deletion
- Deletion marks records as deleted (soft delete)
- Audit logs preserved for compliance
- Hard deletion after retention period

## Observability

### Metrics

**Bill Scanner Metrics**:
- `bill_upload_count`: Counter of uploads by status
- `bill_processing_duration_seconds`: Histogram of processing time
- `ocr_confidence_score`: Histogram of confidence scores
- `extraction_accuracy_percentage`: Gauge of field-level accuracy
- `anomaly_count`: Counter by anomaly type
- `audit_log_write_duration_ms`: Histogram of audit write latency

**Hospital Search Metrics**:
- `search_query_count`: Counter of searches by injury type
- `search_latency_seconds`: Histogram of query response time
- `search_result_count`: Histogram of result counts
- `filter_usage_count`: Counter by filter type
- `click_through_rate`: Gauge of CTR by rank position
- `cache_hit_rate`: Gauge of cache effectiveness

**System Metrics**:
- `api_request_duration_seconds`: Histogram by endpoint
- `api_error_rate`: Counter by error type and endpoint
- `external_api_latency_seconds`: Histogram by provider
- `database_query_duration_seconds`: Histogram by query type
- `queue_depth`: Gauge of pending jobs

### Logging

**Structured Logging Format**:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "service": "bill-scanner",
  "component": "ocr-processor",
  "message": "OCR processing completed",
  "billId": "uuid",
  "userId": "uuid",
  "duration_ms": 2500,
  "confidence": 0.92,
  "traceId": "uuid",
  "spanId": "uuid"
}
```

**Log Levels**:
- ERROR: Processing failures, API errors, data corruption
- WARN: Low confidence, missing data, rate limits
- INFO: Successful operations, state changes
- DEBUG: Detailed processing steps (disabled in production)

### Distributed Tracing

**Trace Propagation**:
- OpenTelemetry for trace context propagation
- Trace ID generated at API gateway
- Span created for each service call
- Trace stored in distributed tracing backend (Jaeger/Tempo)

**Traced Operations**:
- Bill upload → OCR → normalization → anomaly detection
- Search query → NLP → geocoding → ranking → rendering
- External API calls with latency breakdown
- Database queries with execution time

### Alerting

**Critical Alerts** (Page on-call):
- Error rate >5% for 5 minutes
- API latency p99 >10 seconds
- Database connection pool exhausted
- External API completely unavailable
- Disk usage >90%

**Warning Alerts** (Slack notification):
- Error rate >2% for 10 minutes
- Cache hit rate <70%
- OCR confidence <80% for 10 consecutive bills
- Queue depth >1000 jobs

**Health Checks**:
- `/health`: Overall service health
- `/health/ready`: Readiness for traffic
- `/health/live`: Liveness check
- Checks: Database connectivity, external API availability, storage access

## Extensibility

### Adding New Injury/Condition Ontologies

**Current Approach**:
- Injury descriptions mapped to specialties via NLP model
- Specialty database contains condition-to-specialty mappings
- Extensible via configuration without code changes

**Extension Points**:
1. Add new conditions to `medical_conditions` table
2. Map conditions to specialties in `condition_specialty_mapping` table
3. Update NLP model training data with new terms
4. Retrain and deploy updated model

**Example**:
```sql
INSERT INTO medical_conditions (condition_name, synonyms, icd10_codes)
VALUES ('Rotator Cuff Tear', 
        ARRAY['shoulder tear', 'rotator cuff injury'],
        ARRAY['M75.10', 'M75.11']);

INSERT INTO condition_specialty_mapping (condition_id, specialty_id, relevance_score)
VALUES (uuid, 'orthopedics-uuid', 0.95),
       (uuid, 'sports-medicine-uuid', 0.85);
```

### Plugging in Additional OCR/LLM Providers

**Current Architecture**:
- OCR service uses adapter pattern
- Provider configured via environment variables
- Fallback to secondary provider on failure

**Adding New Provider**:
1. Implement `OCRProvider` interface:
```python
class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, document: bytes) -> OCRResult:
        pass
    
    @abstractmethod
    def get_confidence_score(self, result: OCRResult) -> float:
        pass
```

2. Register provider in configuration:
```yaml
ocr:
  primary_provider: google_vision
  fallback_provider: aws_textract
  providers:
    google_vision:
      api_key: ${GOOGLE_VISION_API_KEY}
      endpoint: https://vision.googleapis.com/v1
    aws_textract:
      region: us-east-1
      credentials: ${AWS_CREDENTIALS}
```

3. Deploy with new configuration

### Expanding to New Geographies

**Current Design**:
- Hospital data stored with coordinates
- Distance calculation uses haversine formula (works globally)
- Geocoding supports international addresses

**Geographic Expansion**:
1. Add hospitals for new region to database
2. Configure geocoding service for new country codes
3. Add language support for new region
4. Update SEO content templates for local language
5. Configure CDN edge locations for new region

**Example**:
```sql
INSERT INTO hospitals (name, address, coordinates, country_code, specialties)
VALUES ('Apollo Hospital', 
        '21 Greams Lane, Chennai, Tamil Nadu 600006, India',
        POINT(13.0569, 80.2425),
        'IN',
        ARRAY['cardiology', 'orthopedics', 'neurology']);
```

### Adding Insurance Networks

**Current Design**:
- Hospitals have `insurance_accepted` array
- In-network filter queries this array
- Extensible via hospital data updates

**Adding New Insurance Network**:
1. Update hospital records with new insurance:
```sql
UPDATE hospitals
SET insurance_accepted = array_append(insurance_accepted, 'BlueCross BlueShield')
WHERE hospital_id IN (SELECT hospital_id FROM network_hospitals WHERE network = 'BCBS');
```

2. Add insurance to filter options in UI
3. Update search analytics to track new insurance queries

No code changes required—purely data-driven extension.
