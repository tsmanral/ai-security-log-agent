"""Quick V3 verification script — tests all major components."""
import sys

def verify():
    errors = []
    checks_passed = 0

    # 1. DB Init
    try:
        from ai_sentinel.storage.database import init_db
        init_db()
        print("✅ Database initialization OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"DB init: {e}")
        print(f"❌ Database initialization FAILED: {e}")

    # 2. Severity Scoring
    try:
        from ai_sentinel.detection.severity import compute_severity_score, severity_context
        score, label = compute_severity_score(8.0, 0.95, 3, 3, 0.45)
        ctx = severity_context(score, label)
        assert 0 <= score <= 1
        assert label in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        print(f"✅ Severity scoring OK (score={score:.4f}, label={label})")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Severity: {e}")
        print(f"❌ Severity scoring FAILED: {e}")

    # 3. Auth (bcrypt + JWT)
    try:
        from ai_sentinel.auth import hash_password, verify_password, create_access_token, decode_token
        h = hash_password("testpass")
        assert verify_password("testpass", h)
        assert not verify_password("wrong", h)
        token = create_access_token("u1", "admin", "ADMIN")
        payload = decode_token(token)
        assert payload["sub"] == "u1"
        assert payload["role"] == "ADMIN"
        print(f"✅ Auth (bcrypt + JWT) OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Auth: {e}")
        print(f"❌ Auth FAILED: {e}")

    # 4. Migration runner
    try:
        from ai_sentinel.storage.migration_runner import run_migrations
        from ai_sentinel.storage.database import get_connection
        conn = get_connection()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        required = ["users", "devices", "normalized_events", "anomalies", "incidents",
                     "device_heartbeats", "model_registry", "metrics_5min",
                     "threat_intel_cache", "feature_drift", "ip_geolocation"]
        missing = [t for t in required if t not in tables]
        assert not missing, f"Missing tables: {missing}"
        print(f"✅ Schema migration OK ({len(tables)} tables)")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Migration: {e}")
        print(f"❌ Migration FAILED: {e}")

    # 5. Model persistence
    try:
        from ai_sentinel.models.base_model import BaseAnomalyDetector
        assert hasattr(BaseAnomalyDetector, "save")
        assert hasattr(BaseAnomalyDetector, "load")
        from ai_sentinel.models.autoencoder_model import AutoencoderModel
        ae = AutoencoderModel()
        assert hasattr(ae, "save")
        assert hasattr(ae, "load")
        print("✅ Model persistence methods OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Model persistence: {e}")
        print(f"❌ Model persistence FAILED: {e}")

    # 6. Incident manager
    try:
        from ai_sentinel.detection.incident_manager import IncidentManager
        im = IncidentManager()
        assert im.window_minutes > 0
        print("✅ Incident manager OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Incident manager: {e}")
        print(f"❌ Incident manager FAILED: {e}")

    # 7. Drift detector
    try:
        from ai_sentinel.detection.drift_detector import _calculate_psi
        import numpy as np
        np.random.seed(42)
        ref = np.random.normal(0, 1, 1000)
        cur = np.random.normal(3, 1, 1000)
        psi = _calculate_psi(ref, cur)
        assert psi > 0.2
        print(f"✅ Drift detection OK (PSI={psi:.4f})")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Drift: {e}")
        print(f"❌ Drift detection FAILED: {e}")

    # 8. SHAP aggregator
    try:
        from ai_sentinel.explainability.shap_aggregator import ShapAggregator
        result = ShapAggregator.aggregate_weighted(
            [{"failures_15m": 0.3}, {"failures_15m": 0.9}],
            model_weights=[1.0, 3.0]
        )
        assert abs(result["failures_15m"] - 0.75) < 0.01
        conf = ShapAggregator.mitre_confidence(
            {"failures_15m": 0.8, "unique_users_15m": 0.3, "time_since_last_event_ip": 0.1},
            "T1110.001"
        )
        assert 0 <= conf <= 1
        print(f"✅ SHAP aggregator OK (MITRE confidence={conf:.2f})")
        checks_passed += 1
    except Exception as e:
        errors.append(f"SHAP: {e}")
        print(f"❌ SHAP aggregator FAILED: {e}")

    # 9. Narrative builder
    try:
        from ai_sentinel.explainability.narrative_builder import NarrativeBuilder
        narrative = NarrativeBuilder.build(
            threat_type="Brute Force Attack",
            mitre_id="T1110.001",
            row_data={"source_ip": "1.2.3.4", "effective_username": "admin", "device_id": "d1"},
            layer1_z=5.0,
            layer2_score=0.8,
            layer3_error=0.1,
            severity_context={"severity_score": 0.85, "severity_label": "CRITICAL", "urgency": "Immediate action required."}
        )
        assert "CRITICAL" in narrative
        assert "Brute Force" in narrative
        print("✅ Narrative builder OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Narrative: {e}")
        print(f"❌ Narrative builder FAILED: {e}")

    # 10. Scheduler
    try:
        from ai_sentinel.jobs.scheduler import start_scheduler, stop_scheduler
        print("✅ Scheduler module importable OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Scheduler: {e}")
        print(f"❌ Scheduler import FAILED: {e}")

    # 11. PDF report
    try:
        from ai_sentinel.ui.utils.report_generator import generate_report
        pdf = generate_report(
            title="Test Report",
            kpis={"total_events_24h": 100, "total_anomalies_24h": 5, "open_incidents": 2,
                  "critical_incidents": 1, "active_devices": 3, "total_devices": 5},
        )
        assert len(pdf) > 0
        print(f"✅ PDF export OK ({len(pdf)} bytes)")
        checks_passed += 1
    except Exception as e:
        errors.append(f"PDF: {e}")
        print(f"❌ PDF export FAILED: {e}")

    # 12. Server import
    try:
        from server import app
        assert app.title == "AI-Sentinel V3 API"
        print("✅ Server app import OK")
        checks_passed += 1
    except Exception as e:
        errors.append(f"Server: {e}")
        print(f"❌ Server import FAILED: {e}")

    # Summary
    print(f"\n{'='*60}")
    total = checks_passed + len(errors)
    print(f"  V3 Verification: {checks_passed}/{total} checks passed")
    if errors:
        print(f"  Failures:")
        for err in errors:
            print(f"    ❌ {err}")
    else:
        print("  🎉 All V3 components verified successfully!")
    print(f"{'='*60}")
    return len(errors) == 0


if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
