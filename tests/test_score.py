from jobhunt.score import hard_filter, score_job


def test_hard_filter_rejects_excluded_keyword(base_config, job_factory):
    job = job_factory(description="This is an unpaid internship.")
    passed, reason = hard_filter(job, base_config)
    assert passed is False
    assert "unpaid" in reason.lower()


def test_hard_filter_requires_an_include_keyword(base_config, job_factory):
    job = job_factory(title="Barista", description="Make coffee.")
    passed, reason = hard_filter(job, base_config)
    assert passed is False
    assert "include" in reason.lower()


def test_hard_filter_passes_relevant_job(base_config, job_factory):
    job = job_factory(title="Data Scientist", description="Machine learning role.")
    passed, reason = hard_filter(job, base_config)
    assert passed is True
    assert reason == ""


def test_hard_filter_rejects_remote_only_mismatch(base_config, job_factory):
    base_config.remote_only = True
    job = job_factory(is_remote=False, description="data role on-site")
    passed, reason = hard_filter(job, base_config)
    assert passed is False
    assert "remote" in reason.lower()


def test_hard_filter_rejects_below_salary_floor(base_config, job_factory):
    base_config.salary_min = 50000
    job = job_factory(salary_min=30000, description="data science")
    passed, reason = hard_filter(job, base_config)
    assert passed is False
    assert "salary" in reason.lower()


def test_score_strong_ai_role_scores_high(base_config, job_factory):
    job = job_factory(
        title="AI Engineer",
        description="Python, PyTorch, NLP, deep learning and Docker for our ML team",
    )
    result = score_job(job, base_config)
    assert result.score >= 80
    assert "python" in result.matched
    assert "nlp" in result.matched


def test_score_irrelevant_role_scores_near_zero(base_config, job_factory):
    job = job_factory(
        title="Retail Merchandiser",
        description="Stock shelves and assist retail customers in store",
    )
    result = score_job(job, base_config)
    # 'retail' must NOT match the 'ai' skill (word-boundary matching).
    assert result.score == 0
    assert result.matched == []


def test_score_strong_beats_weak(base_config, job_factory):
    strong = job_factory(description="Python, PyTorch, NLP, deep learning, Docker")
    weak = job_factory(description="General office administration duties")
    assert score_job(strong, base_config).score > score_job(weak, base_config).score


def test_score_matched_is_subset_of_cv_skills(base_config, job_factory):
    job = job_factory(description="Python and FastAPI and unrelated words")
    result = score_job(job, base_config)
    skills = {s.lower() for s in base_config.cv_skills}
    assert set(result.matched).issubset(skills)
