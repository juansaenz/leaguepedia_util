from esports_site import EsportsSite
from datetime import date, timedelta
import mwparserfromhell

overview_text = '<includeonly>{{%s Navbox|year={{#titleparts:{{PAGENAME}}|1|2}}}}</includeonly><noinclude>{{documentation}}</noinclude>'

end_text = '<includeonly>{{#invoke:%s|endTable}}</includeonly><noinclude>{{documentation}}</noinclude>'

date_text = '<includeonly>{{#invoke:%s|date}}</includeonly><noinclude>{{documentation}}</noinclude>'

start_text = '<includeonly>{{#invoke:%s|start}}{{TOCFlat}}</includeonly><noinclude>{{documentation}}</noinclude>'

navbox_text = """{{Navbox
|name={{subst:PAGENAME}}
|title=%s Index
|image=
|state=mw-collapsible

|group1=Years
|list1={{Flatlist}}
{{Endflatlist}}
|group2={{{year|}}}
|list2={{Flatlist}}
{{#switch:{{{year|}}}
}}
{{Endflatlist}}

}}<noinclude>[[Category:Navboxes]]</noinclude>"""

site = EsportsSite('bot', 'cod-esports')  # Set wiki

lookup = {
	"news" : { "template_prefix" : "NewsData",
			   "data_prefix" : "News",
			   "navbox_template" : "NewsData" },
	"ec" : { "template_prefix" : "ExternalContent",
			 "data_prefix" : "ExternalContent",
			 "navbox_template" : "External Content"
			 },
	"rc" : {
		"template_prefix" : "RosterChangeData",
		"data_prefix" : "RosterChanges",
		"navbox_template" : "Roster Change Data"
	}
}

def allsundays(year):
	d = date(year, 1, 1)						  # January 1st
	d += timedelta(days = 6 - d.weekday())  # First Sunday
	while d.year == year:
		yield d
		d += timedelta(days = 7)

def make_data_pages(years, this, startat_page = None):
	passed_startat = True
	if startat_page:
		passed_startat = False
	template_prefix = lookup[this]["template_prefix"]
	data_prefix = lookup[this]["data_prefix"]
	navbox_template = lookup[this]["navbox_template"]
	summary = 'Initializing %s Pages' % template_prefix  # Set summary
	for year in years:
		site.pages['Data:{}/{}'.format(data_prefix, year)].save('{{%sOverview}}' % template_prefix, summary=summary)
		year_switch = '|' + str(year) + '='
		list_of_sundays = [year_switch]
		for d in allsundays(year):
			list_of_sundays.append('* [[Data:{}/{}|{}]]'.format(data_prefix, d.strftime('%Y-%m-%d'), str(d.strftime('%b %d'))))
			
			# START SAVING DATA PAGES - COMMENT THIS BLOCK TO DO NAVBOX ONLY
			page_name = 'Data:{}/{}'.format(data_prefix, str(d))
			if page_name == startat_page:
				passed_startat = True
			if not passed_startat:
				continue
			p = site.pages[page_name]
			if p.exists:
				continue
			lines = [ '{{%s/Start}}' % template_prefix ]
			weekday_index = d
			for i in range(0,7):
				y = weekday_index.year
				m = '{:02d}'.format(weekday_index.month)
				day = '{:02d}'.format(weekday_index.day)
				lines.append('== {} =='.format(weekday_index.strftime('%b %d')))
				lines.append('{{{{{}/Date|y={}|m={}|d={}}}}}'.format(template_prefix, y, m, day))
				weekday_index += timedelta(days = 1)
				lines.append('{{%s/End}}' % template_prefix)
			p.save('\n'.join(lines), summary=summary)
			# END SAVING DATA PAGES - COMMENT THIS BLOCK TO DO NAVBOX ONLY
		
		list_of_sundays.append('}}\n{{Endflatlist}}')
		template_page = site.pages['Template:%s Navbox' % navbox_template]
		wikitext = mwparserfromhell.parse(template_page.text())
		for template in wikitext.filter_templates():
			if template.name.matches('Navbox'):
				text = str(template.get('list1').value.strip())
				list_text = template.get('list2').value.strip()
				if year_switch in list_text:
					break
				text = text.replace('{{Endflatlist}}',
									'* [[Data:{}/{}|{}]]\n{{{{Endflatlist}}}}'.format(data_prefix, str(year), str(year)))
				template.add('list1', text)
				list_text = list_text.replace('}}\n{{Endflatlist}}', '\n'.join(list_of_sundays))
				template.add('list2', list_text)
		template_page.save(str(wikitext))

def make_templates(this):
	template_prefix = lookup[this]["template_prefix"]
	navbox_template = lookup[this]["navbox_template"]
	data_prefix = lookup[this]["data_prefix"]
	summary = 'Initializing %s Pages' % template_prefix  # Set summary
	site.pages['Template:%sOverview' % template_prefix].save(overview_text % navbox_template, summary=summary)
	site.pages['Template:%s/End' % template_prefix].save(end_text % template_prefix, summary=summary)
	site.pages['Template:%s/Date' % template_prefix].save(date_text % template_prefix, summary=summary)
	site.pages['Template:%s Navbox' % navbox_template].save(navbox_text % data_prefix, summary=summary)
	site.pages['Template:%s/Start' % template_prefix].save(start_text % template_prefix, summary=summary)

if __name__ == "__main__":
	this = 'ec'
	# make_templates(this)
	make_data_pages(range(2009,2021), this, startat_page='Data:ExternalContent/2019-11-03')
