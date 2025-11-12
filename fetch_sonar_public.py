"""
Fetch SonarCloud metrics and issues without authentication
Uses public SonarCloud API endpoints
"""
import requests
import json
from datetime import datetime

PROJECT_KEY = "ericfunman_boursicotor"
SONAR_BASE = "https://sonarcloud.io/api"

def fetch_metrics():
    """Get project metrics from SonarCloud public API"""
    print("\n" + "="*70)
    print("📊 FETCHING SONARCLOUD METRICS")
    print("="*70)
    
    try:
        url = f"{SONAR_BASE}/measures/component"
        params = {
            "component": PROJECT_KEY,
            "metricKeys": "coverage,violations,bugs,code_smells,security_hotspots,complexity,duplicated_lines_density,ncloc"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ PROJECT METRICS:")
            print("-" * 70)
            
            if "component" in data:
                component = data["component"]
                
                # Extract measures
                measures = {m["metric"]: m.get("value", "N/A") for m in component.get("measures", [])}
                
                print(f"  Coverage:        {measures.get('coverage', 'N/A')}%")
                print(f"  Violations:      {measures.get('violations', 'N/A')}")
                print(f"  Bugs:            {measures.get('bugs', 'N/A')}")
                print(f"  Code Smells:     {measures.get('code_smells', 'N/A')}")
                print(f"  Security Issues: {measures.get('security_hotspots', 'N/A')}")
                print(f"  Complexity:      {measures.get('complexity', 'N/A')}")
                print(f"  Lines of Code:   {measures.get('ncloc', 'N/A')}")
                
                return measures
        else:
            print(f"❌ API returned {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def fetch_issues_summary():
    """Get issues summary (might require auth for full list)"""
    print("\n" + "="*70)
    print("📋 FETCHING ISSUES SUMMARY")
    print("="*70)
    
    try:
        url = f"{SONAR_BASE}/issues/search"
        params = {
            "componentKeys": PROJECT_KEY,
            "statuses": "OPEN",
            "pageSize": 1  # Just get count
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            
            print(f"\n✅ TOTAL OPEN ISSUES: {total}")
            
            # Try to get breakdown by rule
            print("\n⚠️  Note: Full issue breakdown requires authentication")
            print("   See: https://sonarcloud.io/project/issues?id=" + PROJECT_KEY)
            
            return total
        else:
            print(f"❌ API returned {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def fetch_project_status():
    """Get project analysis status"""
    print("\n" + "="*70)
    print("🔍 FETCHING PROJECT STATUS")
    print("="*70)
    
    try:
        url = f"{SONAR_BASE}/projects/status"
        params = {"projectKey": PROJECT_KEY}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if "projectStatuses" in data and len(data["projectStatuses"]) > 0:
                status = data["projectStatuses"][0]
                
                print(f"\n✅ PROJECT STATUS:")
                print("-" * 70)
                print(f"  Quality Gate: {status.get('qualityGateStatus', 'UNKNOWN')}")
                print(f"  Project Key:  {status.get('key', 'N/A')}")
                
                conditions = status.get("conditions", [])
                if conditions:
                    print(f"\n  Quality Gate Conditions:")
                    for cond in conditions:
                        print(f"    - {cond.get('metricKey', '?')}: {cond.get('actualValue', '?')} {cond.get('status', '?')}")
                
                return status
        else:
            print(f"❌ API returned {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main execution"""
    
    print("\n" + "🔗 " * 25)
    print("SONARCLOUD DATA FETCHER (Public API)")
    print("🔗 " * 25)
    
    print("\n📌 Project: ericfunman_boursicotor")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fetch data
    metrics = fetch_metrics()
    issues = fetch_issues_summary()
    status = fetch_project_status()
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    if metrics:
        print(f"\n✅ Metrics retrieved successfully")
        if metrics.get('violations') != 'N/A':
            violations = int(metrics['violations'])
            print(f"   {violations} violations to fix")
    else:
        print("\n⚠️  Could not fetch metrics")
    
    if issues:
        print(f"\n✅ Issues fetched: {issues} total OPEN issues")
    else:
        print("\n⚠️  Could not fetch issues count")
    
    print("\n" + "="*70)
    print("🌐 VIEW FULL RESULTS IN BROWSER:")
    print("="*70)
    print("\n📊 Dashboard:")
    print("   https://sonarcloud.io/project/overview?id=" + PROJECT_KEY)
    print("\n📋 Issues Details:")
    print("   https://sonarcloud.io/project/issues?id=" + PROJECT_KEY)
    print("\n📈 Metrics:")
    print("   https://sonarcloud.io/project/measures?id=" + PROJECT_KEY)
    
    print("\n💡 TIP: Use the web interface to filter issues by rule")
    print("   (S1192, S7498, S3776, S1481, S117, etc.)")

if __name__ == "__main__":
    main()
