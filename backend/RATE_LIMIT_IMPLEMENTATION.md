# Rate Limit Implementation - Production-Grade Retry Logic

## Problem
- System hit 429 rate limit errors on iteration 7 (after 6-7 API calls in ~30 seconds)
- No retry logic - system gave up immediately
- Anthropic Tier 1 limit: 50 RPM (requests per minute)

## Research Sources (6+)
1. **Anthropic API Documentation** - Token bucket algorithm, retry-after headers
2. **AWS Architecture Blog** - Exponential Backoff & Jitter (Full Jitter best practice)
3. **AWS SDK Retry Behavior** - Standard/Adaptive modes, circuit breaking
4. **OpenAI Python SDK** - `DEFAULT_MAX_RETRIES=2`, jitter implementation
5. **OpenAI Rate Limit Docs** - Error handling patterns
6. **GitHub Copilot patterns** (via OpenAI SDK analysis)

## Key Findings

### Full Jitter Algorithm (AWS)
```
delay = random(0, min(MAX_DELAY, INITIAL_DELAY * 2^retry_count))
```
- **50%+ work reduction** compared to exponential backoff without jitter
- Prevents "thundering herd" problem when multiple clients retry simultaneously
- Reduces request clustering at exponential boundaries

### Industry Standards
- **OpenAI SDK**: 2 retries (3 total attempts), 0.5-8s backoff range
- **AWS SDK**: Standard mode = 3 attempts, circuit breaking enabled
- **Anthropic**: Token bucket algorithm, respect `retry-after` header

### Retry Decision Logic
Retry on:
- 408 (Request Timeout)
- 409 (Conflict)
- 429 (Rate Limit) ← **Our case**
- ≥500 (Server Errors)

Don't retry on:
- 400 (Bad Request)
- 401 (Unauthorized)
- 403 (Forbidden)
- 404 (Not Found)

## Implementation

### RateLimiter Class
Located in `/home/mathijs/Desktop/omni-electron/backend/main.py` (lines 20-137)

**Features**:
1. **Exponential Backoff with Full Jitter**
   - Initial delay: 2.0s (safer than OpenAI's 0.5s for 429s)
   - Max delay: 60s
   - Formula: `random(0, min(max_delay, initial_delay * 2^retry_count))`

2. **Circuit Breaker Pattern**
   - Opens after 5 consecutive failures
   - Timeout: 120 seconds before half-open
   - Prevents cascading failures during API outages

3. **Retry-After Header Respect**
   - Parses `retry-after` header from API responses
   - Validates range (0-300s)
   - Overrides calculated backoff when provided

4. **Request Rate Tracking**
   - Monitors last 100 requests
   - Calculates requests per minute
   - Enables adaptive rate limiting

### Configuration
```python
rate_limiter = RateLimiter(
    max_retries=3,           # 3 retries (4 total attempts)
    initial_delay=2.0,       # Start with 2s delay
    max_delay=60.0,          # Cap at 60s
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=120.0
)
```

### Retry Logic Integration
Located in `chat_streaming` method (lines 555-720)

**Flow**:
1. Check circuit breaker before each attempt
2. Try LLM streaming request
3. On 429 error:
   - Record failure
   - Extract `retry-after` header if present
   - Calculate backoff with jitter
   - Show user feedback: "⏳ *Rate limit bereikt. Wacht X seconden...*"
   - Sleep with backoff
   - Retry (up to 3 times)
4. On success: record success, log RPM
5. On max retries exceeded: raise error

## User Experience

### Before
```
[Iteration 7]
Error: Rate limit exceeded (429)
System stops immediately ❌
```

### After
```
[Iteration 7]
⏳ Rate limit bereikt. Wacht 4 seconden...
[Retry 1/3 after 3.7s backoff]
⏳ Rate limit bereikt. Wacht 11 seconden...
[Retry 2/3 after 10.2s backoff]
✓ Request successful (RPM: 32.5) ✅
[Iteration continues...]
```

## Benefits

1. **Robustness**: Handles transient rate limits gracefully
2. **Performance**: Full jitter reduces contention by 50%+
3. **Future-proof**: 
   - Circuit breaker prevents cascading failures
   - Respects API headers for forward compatibility
   - Adaptive rate tracking enables future optimizations
4. **User-friendly**: Clear feedback during retry delays
5. **Production-grade**: Based on patterns from AWS, OpenAI, Anthropic

## Testing Recommendations

1. **Simulate 429 responses** - Test retry behavior with mock errors
2. **Verify backoff timing** - Confirm exponential pattern (2s, 4s, 8s...)
3. **Check jitter variation** - Ensure random distribution (not fixed delays)
4. **Test retry-after header** - Verify header takes precedence
5. **Circuit breaker activation** - Confirm opens after 5 failures
6. **Max retries exceeded** - Verify graceful error after 3 retries

## Monitoring

The implementation logs:
- Each retry attempt with delay duration
- Circuit breaker state changes
- Request rate (RPM) after successful requests
- Retry-after header usage

Example log output:
```
[RateLimiter] Rate limit hit (429) on iteration 7. Retry 1/3 after 3.7s backoff
[RateLimiter] Request successful (RPM: 32.5)
[RateLimiter] Circuit breaker OPEN after 5 failures. Will retry after 120s
```

## Future Enhancements

1. **Adaptive Rate Limiting**: Use request history to predict limits
2. **Token Bucket Simulation**: Pre-emptively slow down before hitting limit
3. **Distributed Rate Limiting**: Share rate limit state across instances
4. **Prometheus Metrics**: Export retry counts, backoff times, circuit state
5. **A/B Testing**: Compare different jitter strategies (full vs equal vs decorrelated)

## References

- [AWS: Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [AWS SDK: Feature Retry Behavior](https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html)
- [Anthropic: Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [OpenAI Python SDK](https://github.com/openai/openai-python) - Retry implementation
- [OpenAI: Rate Limit Error Handling](https://platform.openai.com/docs/guides/rate-limits)
