from ..models.job import Job

def get_jobs():
    return [
        Job("Software Engineer", "Develop web applications", "Tech Co", "Melbourne", "$100,000"),
        Job("Data Analyst", "Analyze business data", "Data Corp", "Sydney", "$80,000")
    ]