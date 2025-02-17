# weekly is a lie, this runs twice-daily

import mwparserfromhell, datetime
import weekly_utils as utils
from esports_site import EsportsSite
import scrape_runes, luacache_refresh
from template_list import *

site = EsportsSite('me','lol')

limit = -1

site.standard_name_redirects()

# Blank edit pages we need to
blank_edit_pages = ['Leaguepedia:Top Schedule']
for page in blank_edit_pages:
	p = site.pages[page]
	p.save(p.text(), summary = 'blank editing')

now_timestamp = datetime.datetime.utcnow().isoformat()
with open('daily_last_run.txt','r') as f:
	last_timestamp = f.read()
with open('daily_last_run.txt','w') as f:
	f.write(now_timestamp)

revisions = site.api('query', format='json',
					 list='recentchanges',
					 rcstart=now_timestamp,
					 rcend=last_timestamp,
					 rcprop='title|ids|patrolled',
					 rclimit='max',
					 rctoponly=1, # commented bc we need all revisions to patrol user pages
					 rcdir = 'older'
					 )

pages = []
pages_for_runes = []

for revision in revisions['query']['recentchanges']:
	title = revision['title']
	if title not in pages:
		pages.append(title)
		if title.startswith('Data:'):
			pages_for_runes.append(title)

lmt = 1
for page in pages:
	if lmt == limit:
		break
	lmt+=1
	try:
		p = site.pages[page]
	except KeyError:
		print(page)
		continue
	utils.make_doc_pages(site, p)
	if '/Edit Conflict/' in page and p.namespace == 2 and p.text() != '':
		p.delete(reason='Deleting old edit conflict')
	else:
		text = p.text()
		wikitext = mwparserfromhell.parse(text)
		errors = []
		for template in wikitext.filter_templates():
			try:
				if template.name.matches('Infobox Player'):
					utils.fixInfoboxPlayer(template)
					if p.namespace == 0:
						if template.has('checkboxIsPersonality'):
							if template.get('checkboxIsPersonality').value.strip() != 'Yes':
								utils.createResults(site, page, template, 'Tournament Results', 'Player', '{{PlayerResults|show=everything}}')
				elif template.name.matches('Infobox Team'):
					utils.fixInfoboxTeam(template)
					if p.namespace == 0:
						utils.createResults(site, page, template, 'Tournament Results', 'Team', '{{TeamResults|show=everything}}')
						utils.createResults(site, page, template, 'Schedule History', 'Team', '{{TeamScheduleHistory}}')
						tooltip = site.pages['Tooltip:%s' % page]
						tooltip.save('{{RosterTooltip}}',tags='daily_errorfix')
				elif template.name.strip() in gameschedule_templates:
					utils.fixDST(template)
					utils.updateParams(template)
				elif template.name.matches('PicksAndBansS7') or template.name.matches('PicksAndBans'):
					utils.fixPB(site, template)
				elif template.name.matches('Listplayer/Current/End'):
					template.add(1, '')
			except Exception as e:
				errors.append(e)
		if p.namespace == 10008: # Data namespace
			utils.set_initial_order(wikitext)
		newtext = str(wikitext)
		if text != newtext:
			print('Saving page %s...' % page)
			p.save(newtext,summary='Automated error fixing (Python)',tags='daily_errorfix')
		if len(errors) > 0:
			report_page = site.pages['User talk:RheingoldRiver']
			report_errors(report_page, page, errors)
luacache_refresh.teamnames(site)

success_page = site.pages['User:RheingoldRiver/Maint Log']
text = success_page.text()
text = text + '\nScript finished maint successfully: ' + now_timestamp
try:
	scrape_runes.scrape(site, pages_for_runes, False)
	text = text + '\nScript finished regular runes successfully: ' + now_timestamp
except Exception as e:
	text = text + '\nException running regular runes: ' + str(e) + ' ' + now_timestamp
try:
	scrape_runes.scrapeLPL(site, pages_for_runes, False)
	text = text + '\nScript finished everything successfully: ' + now_timestamp
except Exception as e:
	text = text + '\nException running LPL runes: ' + str(e) + ' ' + now_timestamp
success_page.save(text,tags='daily_errorfix')
