from duckduckgo_search import ddg

keywords = 't.aebischer@acutronic-medical.ch'
results = ddg(keywords, region='ch-en', safesearch='Moderate', time='y', max_results=3)
print(results)


