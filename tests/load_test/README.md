# Robust Load Testing for Generative AI Applications

This directory provides a comprehensive load testing framework for your Generative AI application, leveraging the power of [Locust](http://locust.io), a leading open-source load testing tool.

## Using the Makefile (Recommended)

The easiest way to run load tests is using the provided `Makefile` targets. This handles dependencies, environment discovery, and authentication automatically.

### Local Load Testing

```bash
make load-test ENV=dev
```
*Note: This will target your local environment if the Cloud Run service is not found, or you can specify USERS, RATE, and DURATION.*

### Remote Load Testing (Staging/Prod)

```bash
make load-test ENV=staging USERS=50 RATE=5 DURATION=1m
```

This command will:
1. Sync dependencies (including `locust`).
2. Discover the Cloud Run service URL for the specified environment.
3. Obtain a fresh identity token for authentication.
4. Execute Locust in headless mode.
5. Generate reports in `tests/load_test/.results/`.

## Manual Execution (Advanced)

If you prefer manual control, follow these steps:

### Local Load Testing

**1. Start the FastAPI Server:**

Launch the FastAPI server in a separate terminal:

```bash
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload
```

**2. Execute the Load Test:**

```bash
uv run locust -f tests/load_test/load_test.py \
-H http://127.0.0.1:8000 \
--headless \
-t 30s -u 10 -r 2 \
--csv=tests/load_test/.results/results \
--html=tests/load_test/.results/report.html
```

### Remote Load Testing (Targeting Cloud Run)

**1. Obtain Cloud Run Service URL:**

```bash
export RUN_SERVICE_URL=$(gcloud run services describe <service-name> --format='value(status.url)')
```

**2. Obtain ID Token:**

```bash
export _ID_TOKEN=$(gcloud auth print-identity-token -q)
```

**3. Execute the Load Test:**

```bash
_ID_TOKEN=$_ID_TOKEN uv run locust -f tests/load_test/load_test.py \
-H $RUN_SERVICE_URL \
--headless \
-t 30s -u 60 -r 2 \
--csv=tests/load_test/.results/results \
--html=tests/load_test/.results/report.html
```

## Results

Comprehensive CSV and HTML reports detailing the load test performance will be generated and saved in the `tests/load_test/.results` directory.
