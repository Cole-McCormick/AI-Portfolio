"""
Three sample job descriptions for testing the analyzer.
  - GOOD:    Inclusive, clear, unbiased software engineer JD
  - AVERAGE: Mixed quality marketing manager JD
  - POOR:    Biased, vague, off-putting data analyst JD
"""

GOOD_JD = """
Job Title: Software Engineer – Platform Team

About Us
Acme Cloud helps teams ship reliable software faster. We're a fully distributed
team of ~200 people across 14 time zones. We care deeply about building an
environment where everyone can do their best work.

About the Role
We're looking for a Software Engineer to join our Platform team. You'll design
and build the infrastructure that powers our CI/CD pipelines, improve developer
tooling, and collaborate closely with product engineers to unblock their work.

What You'll Do
- Design, build, and maintain scalable backend services (Python / Go)
- Partner with security and infrastructure teams on reliability and compliance
- Write clear documentation so teammates can ramp up quickly
- Participate in an on-call rotation (roughly 1 week per quarter)
- Mentor early-career engineers when you're ready and interested

What We're Looking For
- 3+ years of professional software engineering experience
- Solid understanding of distributed systems principles
- Comfort working in a CI/CD environment (we use GitHub Actions & Terraform)
- Strong written communication – we're async-first
- Curiosity and a collaborative mindset

Nice to Have
- Experience with Kubernetes or container orchestration
- Open-source contributions or public portfolio work

We don't expect you to meet every requirement. If this role excites you,
please apply.

Compensation & Benefits
- Salary: $130,000 – $170,000 (adjusted for your location)
- Equity: 0.05%–0.10% options
- 100% employer-paid medical, dental, and vision
- Unlimited PTO (minimum 15 days encouraged)
- $3,000/year learning & development budget
- Home office stipend: $1,500 to set up your workspace
- Parental leave: 16 weeks for all parents

Interview Process
1. 30-min recruiter screen
2. 45-min technical conversation (no live coding, discussion-based)
3. Take-home project (~4 hours, paid at $150)
4. 2 x 45-min panel interviews (engineering + cross-functional)
5. Offer

We are an equal opportunity employer and are committed to building a diverse
team. We welcome applicants of all backgrounds, identities, and experiences.
Accommodations are available throughout the hiring process — just let us know.
"""

AVERAGE_JD = """
Marketing Manager

We are a fast-growing SaaS company looking for a Marketing Manager to join our
dynamic team. You will be responsible for driving brand awareness and executing
marketing campaigns.

Responsibilities
- Develop and implement marketing strategies
- Manage social media channels and content calendar
- Coordinate with sales team on lead generation
- Analyze campaign performance and report to leadership
- Manage relationships with external agencies and vendors
- Some travel may be required

Requirements
- Bachelor's degree in Marketing, Communications, or related field
- 4-7 years of marketing experience
- Proficiency in marketing automation tools (HubSpot preferred)
- Strong analytical skills and attention to detail
- Excellent communication skills
- Ability to work in a fast-paced environment

Preferred
- Experience in B2B SaaS
- MBA or advanced degree is a plus
- Experience managing a team

What We Offer
- Competitive salary
- Health insurance
- 401(k) with company match
- Flexible work arrangements

We are an equal opportunity employer.
"""

POOR_JD = """
ROCK STAR Data Analyst Needed – Only Serious Applicants

Our rapidly scaling startup is on the hunt for a NINJA data analyst who is
passionate about crushing numbers and moving fast. We need someone who can
hit the ground running from day one – no hand holding here. If you're not a
self-starter who thrives under pressure, this isn't the place for you.

What You'll Be Doing (roughly – things change fast here)
- Pulling reports from our data warehouse
- Lots of ad hoc analysis requests from leadership
- Building dashboards nobody ends up using
- Whatever else comes up

Requirements (non-negotiable, we're very serious about this list)
- 10+ years of experience with Python, SQL, Tableau, Power BI, Spark, R,
  dbt, Looker, Snowflake, BigQuery, Airflow, Excel, and statistics
- Must be a recent grad – we value fresh perspectives
- Bachelor's AND Master's degree required
- Must be available 24/7 and willing to work weekends when needed
- Must be able to physically lift 50 lbs (don't ask)
- Native English speaker required
- No job hoppers – we want loyalty

Culture
We work hard and play hard. We have ping pong tables and free beer on Fridays
(must be 21+). We're like a family here, so drama queens need not apply.
We're a meritocracy so compensation is based purely on results (we don't share
salary bands).

To Apply
Send your resume to jobs@company.com with subject "I am a data ninja."
Applications without the subject line will be deleted automatically.
"""

ALL_JDS = [
    {"label": "Good", "title": "Software Engineer – Platform Team", "text": GOOD_JD},
    {"label": "Average", "title": "Marketing Manager", "text": AVERAGE_JD},
    {"label": "Poor", "title": "Data Analyst (Rock Star Wanted)", "text": POOR_JD},
]
