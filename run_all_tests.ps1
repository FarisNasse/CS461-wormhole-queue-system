pytest
pytest tests/browser --html=tests/browser/reports/performance_report.html --self-contained-html
locust -f tests/load/locustfile.py --headless -u 1000 -r 2 -t 1m