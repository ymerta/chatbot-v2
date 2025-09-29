# App Module Documentation

## Overview

The **App Module** is the core Spring Boot application module of the Netmera platform, serving as the central hub for device management, user operations, messaging, and analytics processing. This module acts as the primary entry point for SDK commands, REST API calls, and various internal operations across the Netmera ecosystem.

## What This Module Does

The App Module handles:

- **Device & User Management**: Registration, tracking, profile updates, and lifecycle management
- **Tag Management**: User segmentation and tagging operations with Adobe Analytics integration
- **Subscription Management**: Trial-to-paid conversions and subscription renewals
- **Coupon Management**: Assignment, expiration, and notification processing
- **Event Processing**: Location events, push notifications, and analytics events
- **Background Jobs**: Scheduled tasks for maintenance, data processing, and external integrations
- **External Integrations**: Adobe Analytics, Google Geofence, and product catalog services

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kafka Topics  │    │   MongoDB       │    │   Hazelcast     │
│   (Commands &   │    │   (User Data)   │    │   (Locks &      │
│    Events)      │    │                 │    │    Cache)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   App Module    │
                    │   (Spring Boot) │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   External APIs │    │   Job Engine    │    │   REST/SDK      │
│   (Adobe, Google)│    │   (Background   │    │   Endpoints     │
│                 │    │    Processing)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Packages & Responsibilities

### 📦 **Main Package** (`com.netmera.app`)
- **`AppMain.java`**: Spring Boot application entry point with Hazelcast client configuration
- **`AppConfiguration.java`**: Core Spring configuration with bean definitions, thread pool executors, and async processing setup

### 🛠️ **Service Package** (`com.netmera.app.service`)

#### **Core Services**
- **`InternalDeviceService`**: Device registration, user management, profile updates, location handling
- **`InternalSubscriptionService`**: Subscription lifecycle management and automatic renewals
- **`InternalTagService`**: User tagging, segmentation, and tag user count management
- **`InternalCouponService`**: Coupon assignment, expiration processing, and notification handling
- **`InternalApplicationService`**: Application-level operations and SDK device registration

#### **Integration Services**
- **`InternalAdobeService`**: Adobe Analytics integration for marketing ID retrieval and user segmentation
- **`GoogleGeofenceService`**: Location-based services and reverse geocoding using Google APIs
- **`ProductCatalogueService`**: E-commerce product catalog synchronization and management

#### **Kafka Consumers**
- **`SdkCommandConsumer`**: Processes SDK commands (device registration, token updates, user operations)
- **`RestCommandConsumer`**: Handles REST API commands with ordered processing
- **`AppInternalCommandConsumer`**: Internal command processing for device tokens and uninstalls
- **`SdkEventConsumer`**: SDK event processing (push opens, rich push actions, location events)
- **`LocationEventConsumer`**: Dedicated location update event processing
- **`UserBatchUpdateConsumer`**: Bulk user profile attribute updates
- **`UserUploadRegisterConsumer`**: User upload registration and file transfer management
- **`UpdateProfileAttributeConsumer`**: Individual profile attribute updates with error handling
- **`AppUserAnalyticConsumer`**: User analytics events with bulk processing

#### **Scheduled Tasks**
- **`AppTasks.java`**: Scheduled maintenance operations including subscription renewals, installation cleanup, coupon expiration, and product catalog synchronization

### 🗄️ **DAO Package** (`com.netmera.app.dao`)
- **`InternalDeviceMongoDao`**: Comprehensive device and user data access with retry mechanisms, migration support, and live activity token management
- **`InternalAppMongoDao`**: Application-specific data access operations
- **`InternalTagMongoDao`**: Tag data access and management
- **`InternalAppJpaDao`**: JPA-based data access for relational operations
- **`InternalAdmCdnDomainsDao`**: CDN domain configuration data access

### 🔧 **Job Package** (`com.netmera.app.job`)
- **`AppJobFactory`**: Factory for creating background job instances based on job type
- **`TagUsersByQueryJob`**: Tags users based on targeting conditions with special report support
- **`TagUserCountRefreshJob`**: Refreshes cached tag user counts
- **`TagAdobeUsersJob`**: Complex parallel processing job for tagging Adobe Analytics users
- **`TagProcessor`**: Interface for batch processing of marketing IDs

### 📊 **Model Package** (`com.netmera.app.model`)
- **`GeofenceServiceResponse`**: Location data response model with hierarchical location information
- **`MigrationRecord`**: User migration tracking between installations
- **`RemoveInstallationRecord`**: Installation removal operations with retry support
- **`SetSourceRetryRecord`**: Source setting retry operations with advertising ID tracking

### 🔧 **Util Package** (`com.netmera.app.util`)
- **`AppConstants`**: Database keys, Hazelcast locks, configuration constants, and timing values
- **`AppUtil`**: ID generation, token validation, ASCII checking, and string utilities

## System Integrations

### 🔄 **Kafka Integration**

#### **Consumer Groups & Configuration**
```java
// High-throughput consumers
APP_SDK_CMDS (100 threads, AT_LEAST_ONCE_BULK)
APP_REST_CMDS (30 threads, AT_MOST_ONCE_BULK)

// Internal processing
APP_INTERNAL_CMDS (10 threads, AT_LEAST_ONCE_BULK)
APP_USER_ANALYTIC (10 threads, AT_LEAST_ONCE_BULK, batch size: 500)

// Bulk operations
APP_USER_UPDATE_BATCH (15 threads, AT_MOST_ONCE_BULK)
APP_USER_UPLOAD_REGISTER (5 threads, AT_LEAST_ONCE_BULK)
APP_PROFILE_ATTRIBUTE (10 threads, AT_LEAST_ONCE_BULK)

// Event processing
APP_SDK_EVENT (10 threads, AT_LEAST_ONCE_BULK)
APP_EVENT_LOCATION (3 threads, AT_LEAST_ONCE_BULK)
```

#### **Key Topics**
- **`CMD_SDK_*`**: SDK commands (device registration, token updates, user operations)
- **`CMD_REST`**: REST API commands with ordered processing
- **`CMD_INTERNAL`**: Internal system commands (device tokens, uninstalls)
- **`USER_BATCH_UPDATE`**: Bulk profile attribute updates
- **`USER_UPLOAD`**: User upload processing and file transfer management
- **`EVENT_SDK`**: SDK events (push opens, rich push actions)
- **`EVENT_LOCATION`**: Location update events
- **`CMD_USER_ANALYTIC`**: User analytics events

### 🗄️ **MongoDB Integration**

#### **Collections**
```javascript
// User Management
COLLECTION_USER: User profiles, attributes, and tracking status
COLLECTION_INSTALLATION: Device installations and tokens

// Tag Management
COLLECTION_APP_TAG: User tags and segments with user counts

// Retry & Migration
COLLECTION_SET_SOURCE_RETRY_RECORDS: Source setting retry operations
COLLECTION_INSTALLATION_REMOVE: Installation removal operations
COLLECTION_MIGRATION: User migration records

// Completed Operations
COLLECTION_INSTALLATION_REMOVE_DONE: Completed removal operations
COLLECTION_MIGRATION_DONE: Completed migration operations
```

#### **Key Operations**
- **Profile Updates**: Atomic updates with set, increment, push, and pull operations
- **Device Management**: Installation tracking, token updates, and uninstall handling
- **Retry Mechanisms**: Automatic retry for failed operations with configurable limits
- **Migration Support**: User data migration between installations

### 🔐 **Hazelcast Integration**

#### **Distributed Locks**
```java
// Scheduled Operations
HZ_LOCK_APP_SUBS_RENEW: Subscription renewal (daily at 00:00)
HZ_LOCK_APP_EXPIRE_COUPONS: Coupon expiration processing
HZ_LOCK_APP_PRODUCT_CATALOGUE: Product catalog synchronization

// Batch Operations
HZ_LOCK_APP_INST_REMOVE: Installation removal processing
HZ_LOCK_APP_INST_SET_SOURCE: Source setting operations
HZ_LOCK_APP_DELETE_BULK_PROFILE: Bulk profile deletion
HZ_LOCK_APP_RETRY_MIGRATION: Migration retry processing
```

#### **Configuration**
- **Client Modes**: MAIN_CLIENT and TARGETING_CLIENT
- **Lock Timeout**: Configurable per operation
- **Cluster Integration**: Multi-node coordination for scheduled tasks

### 🌐 **External APIs**

#### **Adobe Analytics**
- **Marketing ID Retrieval**: Batch processing of segment data
- **Date Range Queries**: Configurable time windows for data extraction
- **Parallel Processing**: Multi-threaded processing for large datasets

#### **Google Geofence**
- **Reverse Geocoding**: Coordinate to location conversion
- **Administrative Boundaries**: Country, city, county, district information
- **API Key Management**: Secure API key handling

#### **Product Catalogs**
- **Synchronization**: Scheduled catalog updates
- **Error Handling**: Retry mechanisms for failed synchronizations

## Configuration

### **Thread Pool Configuration**
```java
// Batch Scheduler (10 threads)
@Bean(name = "batchScheduler")
public Executor taskExecutor() {
    return Executors.newScheduledThreadPool(10);
}

// Batch Executor (5-10 threads, CallerRunsPolicy)
@Bean(name = "batchExecutor")
public Executor batchExecutor() {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(5);
    executor.setMaxPoolSize(10);
    executor.setQueueCapacity(10);
    executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
    return executor;
}
```

### **Application Properties**
```properties
# Skip subscription renewal (for specific servers)
skipRenew=false

# Retry configuration
app.setSource.maxRetry=10
app.refresh.rate.localCubes=60000
app.time.oneHour=3600000

# External API configuration
adobe.analytics.apiKey=<key>
google.geofence.apiKey=<key>
```

### **Environment Variables**
- **Database**: MongoDB connection strings and pool settings
- **Kafka**: Broker configurations and topic settings
- **Hazelcast**: Cluster configuration and client settings
- **External APIs**: API keys and endpoint configurations

## For New Developers

### 🚀 **Getting Started**

1. **Entry Point**: Start with `AppMain.java` to understand the application bootstrap
2. **Configuration**: Review `AppConfiguration.java` for Spring bean setup and integrations
3. **Data Flow**: Follow a device registration flow:
   ```
   SDK → SdkCommandConsumer → InternalDeviceService → InternalDeviceMongoDao → MongoDB
   ```

### 📚 **Code Reading Path**

#### **Phase 1: Foundation**
1. **`AppMain.java`** - Application entry point and Hazelcast configuration
2. **`AppConfiguration.java`** - Spring configuration and bean definitions
3. **`AppConstants.java`** - System constants and configuration values

#### **Phase 2: Core Services**
1. **`InternalDeviceService.java`** - Service interface (160 methods)
2. **`InternalDeviceServiceImpl.java`** - Core implementation (3,398 lines)
3. **`InternalDeviceMongoDao.java`** - Data access interface
4. **`InternalDeviceMongoDaoImpl.java`** - MongoDB operations implementation

#### **Phase 3: Message Processing**
1. **`SdkCommandConsumer.java`** - SDK command processing
2. **`OrderedQueueConsumer`** vs **`InternalUnOrderedQueueConsumer`** patterns
3. **`AppInternalCommandConsumer.java`** - Internal command handling

#### **Phase 4: Background Processing**
1. **`AppJobFactory.java`** - Job creation patterns
2. **`TagUsersByQueryJob.java`** - Query-based tagging
3. **`TagAdobeUsersJob.java`** - Complex parallel processing
4. **`AppTasks.java`** - Scheduled task management

### 🔧 **Development Patterns**

#### **Service Implementation Pattern**
```java
@Service
public class InternalDeviceServiceImpl implements InternalDeviceService {
    
    @Autowired
    private InternalDeviceMongoDao deviceDao;
    
    @Override
    public void handleCommand(SdkRegisterDeviceCmd cmd) {
        // 1. Validate command parameters
        if (!isValidCommand(cmd)) {
            logger.warn("Invalid command: {}", cmd);
            return;
        }
        
        // 2. Execute business logic
        Device device = processDeviceRegistration(cmd);
        
        // 3. Persist changes
        deviceDao.saveDevice(device);
        
        // 4. Publish events if needed
        publishDeviceRegisteredEvent(device);
    }
}
```

#### **Consumer Pattern**
```java
@Component
public class SdkCommandConsumer extends OrderedQueueConsumer {
    
    public SdkCommandConsumer() {
        super(CONSUMER_GROUP, TOPIC_PATTERN, PARALLELISM, OFFSET_STRATEGY);
    }
    
    @Override
    public void process(SdkRegisterDeviceCmd cmd) {
        logger.info("Processing command: {}", cmd);
        try {
            deviceService.handleCommand(cmd);
        } catch (Exception e) {
            logger.error("Command processing failed", e);
            // Handle error appropriately
        }
    }
}
```

#### **Job Implementation Pattern**
```java
public class TagUsersByQueryJob extends NmJob {
    
    private String appKey;
    private String tagName;
    private Conditions conditions;
    
    @Override
    public boolean prepareAndValidate() {
        JobParameters params = jobExecution.getParameters();
        appKey = params.getString(JOB_PARAM_KEY_APP_KEY);
        tagName = params.getString(JOB_PARAM_KEY_TAG_NAME);
        conditions = params.readObject(JOB_PARAM_KEY_CONDITIONS_BINARY, Conditions.class);
        
        return appKey != null && tagName != null && conditions != null;
    }
    
    @Override
    public void execute() {
        logger.info("Starting job: appKey={}, tagName={}", appKey, tagName);
        
        AppTag tag = tagService.findTagByName(appKey, tagName, null);
        targetingService.assignTag(appKey, tag.getId(), conditions.asList());
        
        logger.info("Job completed successfully");
    }
}
```

### 🎯 **Key Concepts**

#### **Commands vs Events**
- **Commands**: Modify system state (device registration, profile updates)
- **Events**: Notifications of state changes (push opens, location updates)

#### **Ordered vs Unordered Processing**
- **Ordered**: Location events, subscription operations (consistency required)
- **Unordered**: Profile updates, analytics events (performance optimized)

#### **Retry Mechanisms**
- **Automatic**: Failed operations stored in retry collections
- **Configurable**: Maximum retry counts and intervals
- **Monitoring**: Retry queue health and success rates

## Common Failure Scenarios & Debugging

### 🚨 **High-Priority Issues**

#### **1. Kafka Consumer Lag**
**Symptoms**: Delayed processing, accumulating messages
```bash
# Check consumer lag
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group APP_SDK_CMDS

# Monitor processing rates
grep "Processing command" /var/log/app/*.log | tail -1000
```

**Common Causes**:
- Database connection issues
- Slow external API calls
- Memory pressure
- Thread pool exhaustion

**Solutions**:
- Increase consumer parallelism
- Optimize database queries
- Implement circuit breakers for external calls
- Monitor memory usage and GC patterns

#### **2. MongoDB Performance Issues**
**Symptoms**: Slow queries, connection timeouts, high CPU usage
```bash
# Check slow queries
db.setProfilingLevel(2, { slowms: 100 })
db.getProfilingData().limit(5).sort({ $natural: -1 })

# Monitor connection pool
grep "connection pool" /var/log/app/*.log
```

**Common Causes**:
- Missing indexes
- Large collection scans
- Connection pool exhaustion
- Write conflicts

**Solutions**:
- Add appropriate indexes
- Optimize query patterns
- Increase connection pool size
- Use bulk operations for large updates

#### **3. Hazelcast Cluster Issues**
**Symptoms**: Lock timeouts, cluster partition, service unavailability
```bash
# Check cluster health
hz-cluster-admin -o cluster-state

# Monitor lock acquisition
grep "HZ_LOCK_APP" /var/log/app/*.log
```

**Common Causes**:
- Network partitions
- Long-running operations holding locks
- Cluster member failures
- Configuration mismatches

**Solutions**:
- Verify network connectivity
- Implement lock timeouts
- Monitor cluster member health
- Review Hazelcast configuration

#### **4. Job Execution Failures**
**Symptoms**: Jobs stuck, high failure rates, resource exhaustion
```bash
# Monitor job execution
grep "Job execution" /var/log/app/*.log | grep -E "(FAILED|ERROR)"

# Check job queue status
# Monitor job engine metrics
```

**Common Causes**:
- Invalid job parameters
- External service failures
- Resource constraints
- Database lock contention

**Solutions**:
- Validate job parameters thoroughly
- Implement retry mechanisms
- Monitor resource usage
- Use appropriate isolation levels

### 🔍 **Debugging Tools & Techniques**

#### **Log Analysis Patterns**
```bash
# Device registration flow
grep -A 5 -B 5 "SdkRegisterDeviceCmd" /var/log/app/*.log

# Tag processing issues
grep -E "(TagUsersByQueryJob|TagAdobeUsersJob)" /var/log/app/*.log

# Subscription renewal problems
grep "renewSubscriptions" /var/log/app/*.log | grep -E "(ERROR|WARN)"

# Consumer lag issues
grep "consumer lag" /var/log/app/*.log
```

#### **Database Debugging**
```javascript
// Check user registration status
db.user.findOne({"_id": "user_id"}, {"profile": 1, "untracked": 1})

// Monitor tag assignments
db.appTag.find({"appKey": "app_key"}).sort({"updateDate": -1})

// Check retry operations
db.setSourceRetryRecords.find({"ak": "app_key", "retry": {"$gt": 5}})

// Monitor installation status
db.installation.find({"appKey": "app_key", "installed": true}).count()
```

#### **Performance Monitoring**
```bash
# Memory usage
jstat -gc <pid> 5s

# Thread analysis
jstack <pid> | grep -A 10 -B 10 "BLOCKED"

# Database connection monitoring
netstat -an | grep :27017 | wc -l
```

### 📋 **Health Check Checklist**

#### **System Health**
- [ ] All Kafka consumers processing (lag < 1000)
- [ ] MongoDB connections healthy (< 80% pool utilization)
- [ ] Hazelcast cluster fully connected
- [ ] Memory usage stable (< 80% heap)
- [ ] No critical errors in logs

#### **Business Logic Health**
- [ ] Device registration success rate > 95%
- [ ] Tag processing completing successfully
- [ ] Subscription renewals running daily
- [ ] Coupon expiration processing
- [ ] External API calls succeeding

#### **Performance Metrics**
- [ ] Average response time < 100ms
- [ ] Database query performance acceptable
- [ ] Job execution success rate > 95%
- [ ] No deadlocks or long-running locks

## Best Practices

### 🏗️ **Development Guidelines**

#### **Command Processing**
```java
// Always validate input
@Override
public void handleCommand(SdkRegisterDeviceCmd cmd) {
    if (!isValidAppKey(cmd.getAppKey())) {
        logger.warn("Invalid app key: {}", cmd.getAppKey());
        return;
    }
    
    // Process with proper error handling
    try {
        processDeviceRegistration(cmd);
    } catch (Exception e) {
        logger.error("Registration failed for device: {}", cmd.getDeviceId(), e);
        // Implement appropriate error handling
    }
}
```

#### **Database Operations**
```java
// Use transactions for multi-step operations
@Transactional
public void migrateUserData(String oldUserId, String newUserId) {
    // All operations succeed or fail together
    userDao.updateUserId(oldUserId, newUserId);
    installationDao.updateUserId(oldUserId, newUserId);
    tagDao.updateUserId(oldUserId, newUserId);
}

// Implement proper retry logic
@Retryable(value = {MongoException.class}, maxAttempts = 3)
public void saveUserProfile(User user) {
    userDao.save(user);
}
```

#### **Job Implementation**
```java
// Design for idempotency
@Override
public void execute() {
    // Check if job already completed
    if (isJobAlreadyCompleted()) {
        logger.info("Job already completed, skipping");
        return;
    }
    
    // Process with proper state management
    markJobInProgress();
    try {
        executeJobLogic();
        markJobCompleted();
    } catch (Exception e) {
        markJobFailed();
        throw e;
    }
}
```

### 🔒 **Security Considerations**

1. **Input Validation**: Always validate and sanitize external input
2. **Authentication**: Verify API keys and tokens
3. **Rate Limiting**: Implement limits for expensive operations
4. **Data Privacy**: Handle PII according to regulations
5. **Logging**: Avoid logging sensitive information

### 📈 **Performance Optimization**

1. **Batch Processing**: Use bulk operations for large datasets
2. **Connection Pooling**: Optimize database connection pools
3. **Caching**: Cache frequently accessed data
4. **Async Processing**: Use async operations where appropriate
5. **Monitoring**: Implement comprehensive monitoring

## Testing Strategy

### 🧪 **Unit Tests**
```java
@Test
public void testDeviceRegistration() {
    // Given
    SdkRegisterDeviceCmd cmd = createValidCommand();
    when(deviceDao.findByDeviceId(cmd.getDeviceId())).thenReturn(null);
    
    // When
    deviceService.handleCommand(cmd);
    
    // Then
    verify(deviceDao).saveDevice(argThat(device -> 
        device.getDeviceId().equals(cmd.getDeviceId())));
}
```

### 🔄 **Integration Tests**
```java
@SpringBootTest
@TestPropertySource(properties = {
    "spring.kafka.bootstrap-servers=${spring.embedded.kafka.brokers}"
})
public class DeviceRegistrationIntegrationTest {
    
    @Test
    public void testCompleteRegistrationFlow() {
        // Test SDK command → Consumer → Service → DAO → Database
        SdkRegisterDeviceCmd cmd = createTestCommand();
        
        // Send command to Kafka
        kafkaTemplate.send("cmd-sdk-register", cmd);
        
        // Verify database state
        await().untilAsserted(() -> {
            Device device = deviceDao.findByDeviceId(cmd.getDeviceId());
            assertThat(device).isNotNull();
            assertThat(device.isRegistered()).isTrue();
        });
    }
}
```

### 📊 **Performance Tests**
```java
@Test
public void testHighThroughputProcessing() {
    // Generate load and measure performance
    int messageCount = 10000;
    List<SdkRegisterDeviceCmd> commands = generateTestCommands(messageCount);
    
    long startTime = System.currentTimeMillis();
    
    commands.parallelStream().forEach(cmd -> {
        deviceService.handleCommand(cmd);
    });
    
    long duration = System.currentTimeMillis() - startTime;
    double throughput = messageCount / (duration / 1000.0);
    
    assertThat(throughput).isGreaterThan(100); // messages per second
}
```

## Deployment & Operations

### 📦 **Build Process**
```bash
# Build the module
./gradlew :modules:app:build

# Run tests
./gradlew :modules:app:test

# Create distribution
./gradlew :modules:app:distTar
```

### 🚀 **Environment Configuration**

#### **Development**
```properties
# Reduced parallelism for debugging
kafka.consumer.app.sdk.parallelism=1
kafka.consumer.app.rest.parallelism=1

# Verbose logging
logging.level.com.netmera.app=DEBUG
logging.level.org.springframework.kafka=DEBUG
```

#### **Production**
```properties
# Optimized settings
kafka.consumer.app.sdk.parallelism=100
kafka.consumer.app.rest.parallelism=30

# Performance logging
logging.level.com.netmera.app=INFO
logging.level.org.springframework.kafka=WARN
```

### 🔄 **Deployment Strategy**

1. **Pre-deployment Checks**:
    - Verify database connectivity
    - Check Kafka cluster health
    - Validate configuration files
    - Review recent error logs

2. **Rolling Deployment**:
    - Deploy to single instance
    - Monitor consumer lag and error rates
    - Gradually expand to all instances
    - Monitor system health metrics

3. **Post-deployment Validation**:
    - Verify all consumers are processing
    - Check database operations
    - Monitor external API calls
    - Validate scheduled tasks

### 📊 **Monitoring & Alerting**

#### **Key Metrics**
- Consumer lag per topic
- Database connection pool utilization
- Job execution success rates
- Memory and CPU usage
- External API response times

#### **Alert Thresholds**
- Consumer lag > 5000 messages
- Database connection pool > 90%
- Job failure rate > 5%
- Memory usage > 85%
- Error rate > 1%

---

## Quick Reference

### 📞 **Critical Service Methods**
```java
// Device Management
InternalDeviceService.handleCommand(SdkRegisterDeviceCmd)
InternalDeviceService.handleLocationEvent(NmSdkEvent)
InternalDeviceService.untrackUser(String, String)

// Tag Management
InternalTagService.setUserCount(String, int, int)
TagUsersByQueryJob.execute()

// Subscription Management
InternalSubscriptionService.renewSubscriptions()

// Coupon Management
InternalCouponService.handleCommand(CouponAssignedCmd)
InternalCouponService.expireCoupons(String)
```

### 🎯 **Key Consumers & Topics**
```java
// High-volume consumers
SdkCommandConsumer     → CMD_SDK_*        (100 threads)
RestCommandConsumer    → CMD_REST         (30 threads)
SdkEventConsumer       → EVENT_SDK        (10 threads)

// Batch processing
UserBatchUpdateConsumer → USER_BATCH_UPDATE (15 threads)
AppUserAnalyticConsumer → CMD_USER_ANALYTIC (10 threads)

// Specialized processing
LocationEventConsumer   → EVENT_LOCATION   (3 threads)
UpdateProfileAttributeConsumer → CMD_PROFILE_ATTR_* (10 threads)
```

### 🔧 **Scheduled Tasks**
```java
// Daily at 00:00 UTC
@Scheduled(cron = "0 0 0 * * ?")
public void executeRenewSubscriptionsTask()

// Every 10 minutes
@Scheduled(fixedDelay = 600000)
public void executeInstallationRemovalTask()

// Every hour
@Scheduled(fixedRate = 3600000)
public void executeExpireCouponsTask()
```

### 🗄️ **Database Collections**
```javascript
// Primary collections
db.user                    // User profiles and tracking
db.installation           // Device installations
db.appTag                 // User tags and segments

// Retry collections
db.setSourceRetryRecords  // Source setting retries
db.installationRemove     // Installation removal retries
db.migration              // User migration retries
```

### 🔐 **Hazelcast Locks**
```java
// Scheduled operation locks
HZ_LOCK_APP_SUBS_RENEW           // Subscription renewal
HZ_LOCK_APP_EXPIRE_COUPONS       // Coupon expiration
HZ_LOCK_APP_PRODUCT_CATALOGUE    // Product catalog sync

// Batch operation locks
HZ_LOCK_APP_INST_REMOVE          // Installation removal
HZ_LOCK_APP_DELETE_BULK_PROFILE  // Bulk profile deletion
HZ_LOCK_APP_RETRY_MIGRATION      // Migration retry
```

For additional support, refer to the comprehensive JavaDoc documentation in each class or contact the platform engineering team.