from __future__ import division, print_function
import sys
import copy
import smtplib
import ssl
from config import *

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_QUERY = {
    "bug_status": None,
    "f3": "OP",
    "f6": "CP",
    "f8": "flagtypes.name",
    "j3": "OR",
    "o8": "anywordssubstr",
    "query_format": "advanced",
    "classification": "Red Hat",
    "product": BUGZILLA_PRODUCT,
    "v8": ""
}


def send_email(gmail_user, gmail_password, recipients, subject, body):

    sent_from = gmail_user

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = ", ".join(recipients)

    # Create the body of the message (a plain-text and an HTML version).
    text = body

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, recipients, msg.as_string())
        server.close()

        print('Email sent!')
    except:
        print('Something went wrong...{}', sys.exc_info()[0])


def all_members():
    memb_list = teams.values()
    return [mem for team in memb_list for mem in team]


def all_bugs(bugs_dict):
    bug_list = bugs_dict.values()
    return [bug for comp in bug_list for bug in comp]


def get_bug_url_link(bug_ids):
    return (
        "https://bugzilla.redhat.com/buglist.cgi?bug_id={}".format(
            ','.join(bug_ids)
        )
    )

def report_needinfos():
    team_bugs = []
    needinfos = get_needinfos_bugs()
    all_team_members = all_members()

    for bug in needinfos:
        bug_flags = bug.flags[0]
        requestee = bug_flags.get('requestee')
        try:
            req = requestee.split("@")[0]
            if req in all_team_members:
                team_bugs.append(bug)
        except AttributeError as ex:
            print(
                "No needinfo contact for bug {}".format(bug.id)
            )

    for bug in team_bugs:
        short_url = get_bug_url_link([str(bug.id)])
        link = "<a href='{}' target='_blank'>(Link)".format(short_url)
        print(
            "<li>{} [{}] [{}]: {}  {}</li>".format(
                bug.bug_id, bug.status, bug.flags[0].get('requestee').split("@")[0], bug.summary, link
            )
        )



def report_status_on_qa(version):
    on_qa = get_on_qa_bugs(version=version)
    total_on_qa = len(on_qa)
    bug_id_list = [str(bug.id) for bug in on_qa]
    short_url = get_bug_url_link(bug_id_list)
    link = ""
    if len(bug_id_list):
        link = "<a href='{}' target='_blank'>(Link)".format(short_url)
    print(
        "<h3>Total ON_QA: {} {}</h3>".format(total_on_qa, link)
    )


def report_new_arrivals():
    new_bugs = get_new_arrivals()
    new_bugs = filter_by_component(new_bugs)
    total_new = len(all_bugs(new_bugs))
    print(
        "<h3>New arrivals (weekly): {}</h3>".format(total_new)
    )
    for comp, bugs in new_bugs.iteritems():
        bug_id_list = []
        bugs.sort(key=lambda x: severity[x.bug_severity])
        if bugs:
            print(
                "<u><b><ul style='padding-left:10px;'>Component {} bugs:"
                "</ul></b></u>".format(comp, len(bugs))
            )
        for new_bug in bugs:
            print("<li>Bug {} [{}] [{}]: {}</li>".format(
                new_bug.bug_id, new_bug.bug_severity, new_bug.status,
                new_bug.short_desc
            ))
            bug_id_list.append(str(new_bug.bug_id))
        if len(bug_id_list) > 0:
            bug_link = get_bug_url_link(bug_ids=bug_id_list)
            link = "<a href='{}' target='_blank'>here".format(bug_link)
            print("<p>&nbsp;&nbsp;&nbsp;Link to bugs: {}</p>".format(link))

def report_resolved_bugs():
    resolved_bugs = get_resolved_bugs()
    resolved_bugs = filter_by_component(resolved_bugs)
    total_new = len(all_bugs(resolved_bugs))
    print(
        "<h3>Resolved bugs (weekly): {}</h3>".format(total_new)
    )

def report_open_blockers(version):
    open_blockers = get_open_blockers(version=version)
    open_blockers = filter_by_status(open_blockers, OPEN_BUGS)
    open_blockers = filter_by_component(open_blockers)
    total_blockers = len(all_bugs(open_blockers))
    print(
        "<h3>Open Blocker+: {}</h3>".format(total_blockers)
    )
    for comp, bugs in open_blockers.iteritems():
        bug_id_list = []
        bugs.sort(key=lambda x: severity[x.bug_severity])
        if bugs:
            print(
                "<u><b><ul style='padding-left:10px;'>Component {} bugs:"
                "</ul></b></u>".format(comp, len(bugs))
            )
        for blocker in bugs:
            print("<li>Bug {} [{}] [{}]: {}</li>".format(
                blocker.bug_id, blocker.bug_severity, blocker.status,
                blocker.short_desc
            ))
            bug_id_list.append(str(blocker.bug_id))
        if len(bug_id_list) > 0:
            bug_link = get_bug_url_link(bug_ids=bug_id_list)
            link = "<a href='{}' target='_blank'>here".format(bug_link)
            print("<p>&nbsp;&nbsp;&nbsp;Link to bugs: {}</p>".format(link))


def report_open_candidate_blockers(version):
    open_blockers = get_open_candidate_blockers(version=version)
    open_blockers = filter_by_status(open_blockers, OPEN_BUGS)
    open_blockers = filter_by_component(open_blockers)
    total_blockers = len(all_bugs(open_blockers))
    print(
        "<h3>Open Blocker?: {}</h3>".format(total_blockers)
    )

    for comp, bugs in open_blockers.iteritems():
        bug_id_list = []
        bugs.sort(key=lambda x: severity[x.bug_severity])
        if bugs:
            print("<u><b><ul style='padding-left:10px;'>Component {} bugs:"
                "</ul></b></u>".format(comp, len(bugs))
            )
        for blocker in bugs:
            print("<li>Bug {} [{}] [{}]: {}</li>".format(
                blocker.bug_id, blocker.bug_severity, blocker.status,
                blocker.short_desc
            ))
            bug_id_list.append(str(blocker.bug_id))
        if len(bug_id_list) > 0:
            bug_link = get_bug_url_link(bug_ids=bug_id_list)
            link = "<a href='{}' target='_blank'>here".format(bug_link)
            print("<p>&nbsp;&nbsp;&nbsp;Link to bugs: {}</p>".format(link))

def filter_by_component(bugs, verify_status=True):
    bugs_by_comp = copy.deepcopy(COMPONENTS)
    for bug in bugs:
        if verify_status and not (
            bug.status in OPEN_BUGS or bug.status in (
                VERIFIED or bug.status in ON_QA
            )
        ):
            continue
        if bug.component in bugs_by_comp:
            bugs_by_comp[bug.component].append(bug)
        else:
            continue
    return bugs_by_comp

def report_missing_acks(version, team=all_team):
    def print_report(team_bugs):
        bug_list = []
        for bug in team_bugs:
            try:
                print(
                    "<li>Bug {} [{}]: {}</li>".format(
                        bug.bug_id, bug.qa_contact.split("@")[0], bug.short_desc
                    )
                )
                bug_list.append(str(bug.id))
            except AttributeError as ex:
                print("No needinfo contact for bug {}".format(bug.id))

        short_url = get_bug_url_link(bug_list)
        link = "<a href='{}' target='_blank'>here".format(short_url)
        print(
            "<p>&nbsp;&nbsp;&nbsp;Link to bugs: {}</p>".format(link)
        )
    missing_acks = get_missing_acks(version=version)
    total_missing_acks = len(missing_acks)
    if team == all_team and total_missing_acks > 0:
        team_bugs = filter_by_team(bugs=missing_acks)
        for team, bugs in team_bugs.iteritems():
            bug_id_list = [str(bug.id) for bug in bugs]
            short_url = get_bug_url_link(bug_id_list)
            link = ""
            if len(bug_id_list) > 0:
                link = "<a href='{}' target='_blank'>(Link)".format(short_url)
                print(
                    "<u><b><ul style='padding-left:10px;'>Team {} total "
                    "missing acks: {} - "
                    "</ul></b></u>".format(team, len(bugs), link)
                )
                print_report(bugs)


# def filter_by_component(bugs):
#     bugs_by_comp = copy.deepcopy(COMPONENTS)
#     for bug in bugs:
#         if not (
#             bug.status in OPEN_BUGS or bug.status in (
#                 VERIFIED or bug.status in ON_QA
#             )
#         ):
#             continue
#         if bug.component in bugs_by_comp:
#             bugs_by_comp[bug.component].append(bug)
#         else:
#             continue
#     return bugs_by_comp


def filter_by_team(bugs):
    bugs_by_team = copy.deepcopy(BUGS_BY_TEAM)
    for bug in bugs:
        if not (
            bug.status in OPEN_BUGS or bug.status in (
                VERIFIED or bug.status in ON_QA
            )
        ):
            continue
        try:
            qa_contact = bug.qa_contact_detail['email'].split('@')[0]
            if qa_contact in all_members():
                for team, members in teams.iteritems():
                    if qa_contact in members:
                        bugs_by_team[team].append(bug)
        except AttributeError as ex:
            print("No needinfo contact for bug {}".format(bug.id))

    return bugs_by_team


def filter_by_status(bugs, status):
    return [bug for bug in bugs if bug.status in status]


def filter_by_severity(bugs, severity):
    return [bug for bug in bugs if bug.bug_severity in severity]


def filter_by_resolution(bugs, resolution):
    return [bug for bug in bugs if bug.resolution in resolution]

def filter_by_no_keywords(bugs, keywords):
    filtered_list = []
    for bug in bugs:
        if not any(x in bug.keywords for x in keywords):
            filtered_list.append(bug)
    return filtered_list

def report_on_qa_blockers():

    def print_report(bugs):
        bug_list = []
        bugs.sort(key=lambda x: severity[x.bug_severity])
        print("<ul style='list-style-type:circle'>")
        for bug in bugs:
            print(
                "<li>Bug {} [{}]: {}</li>".format(
                    bug.bug_id, bug.bug_severity, bug.short_desc
                )
            )
            bug_list.append(str(bug.id))
        print("</ul>")
        if len(bug_list) > 0:
            short_url = get_bug_url_link(bug_list)
            link = "<a href='{}' target='_blank'>here".format(short_url)
            print(
                "<p>&emsp;&emsp;&emsp;Link to bugs: {}</p>".format(link)
            )

    on_qa_blockers = get_on_qa_blockers(version=version)
    total_on_qa_blockers = len(on_qa_blockers)
    bug_id_list = [str(bug.id) for bug in on_qa_blockers]
    short_url = get_bug_url_link(bug_id_list)
    link = ""
    if len(bug_id_list) > 0:
        link = "<a href='{}' target='_blank'>(Link)".format(short_url)
    print(
        "<h3>ON_QA Blocker+: {} {}</h3>".format(total_on_qa_blockers, link)
    )
    print_report(on_qa_blockers)


def get_needinfos_bugs():
    all_team_members = all_members()
    all_team_members = ",".join(all_team_members)
    query = {
        "bug_status" : "",
        "classification" : "Red Hat",
        "f1" : "requestees.login_name",
        "f2" : "flagtypes.name",
        "include_fields" : [
            "id",
            "keywords",
            "flags",
            "summary",
            "flags_all",
            "qa_contact",
            "qa_contact_realname",
            "short_desc",
            "short_short_desc",
            "status",
            "whiteboard",
            "changeddate",
            "severity",
            "target_milestone"
        ],
        "o1" : "anywordssubstr",
        "o2" : "substring",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "v1" : all_team_members,
        "v2" : "needinfo"
    }
    bugs = bzapi.query(query)
    return filter_only_bugs(bugs)


def sort_target_release(bugs):
    target_release = {}
    for bug in bugs:
        if bug.target_milestone in target_release:
            target_release[bug.target_milestone].append(bug)
        else:
            target_release[bug.target_milestone] = [bug]
    return target_release


def sort_by_pm_score(bugs):
    return sorted(bugs, key=lambda x: int(x.cf_pm_score), reverse=True)


def filter_only_bugs(bug_list):
    filtered_list = []
    for bug in bug_list:
        if "FutureFeature" in bug.keywords or "Improvement" in bug.keywords:
            continue
        else:
            filtered_list.append(bug)
    return filtered_list


def get_new_arrivals(version=VERSION, changed_from='-1w', changed_to="Now"):
    query = {
        "action": "wrap",
        "chfield" : "[Bug creation]",
        "chfieldfrom" : changed_from,
        "chfieldto" : changed_to,
        "f3": "OP",
        "f6": "CP",
        "f7": "component",
        "j3": "OR",
        "o7": "notsubstring",
        "query_format": "advanced",
        #"target_release": "---",
        "classification": "Red Hat",
        "product": BUGZILLA_PRODUCT,
        "v7": "documentation",
        "version": version
    }
    bugs = bzapi.query(query)
    return filter_only_bugs(bugs)


def get_blocker_arrivals(version=VERSION, changed_from='-1w', changed_to="Now"):
    query = {
        "bug_status": "",
        "chfield": "[Bug creation]",
        "chfieldfrom": changed_from,
        "chfieldto": changed_to,
        "f3": "OP",
        "f6": "CP",
        "f7": "flagtypes.name",
        "j3": "OR",
        "o7": "anywordssubstr",
        "query_format" : "advanced",
        "classification": "Red Hat",
        "product": BUGZILLA_PRODUCT,
        "v7": "blocker+ blocker?",
        "f8": "component",
        "o8": "notsubstring",
        "v8": "documentation",
        "version": version
    }
    bugs = bzapi.query(query)
    return filter_only_bugs(bugs)


def get_resolved_bugs(
    version=VERSION, changed_from='-1w', changed_to="Now"
):
    query = {
        "bug_status": "",
        "chfield": "bug_status",
        "chfieldfrom": changed_from,
        "chfieldto": changed_to,
        "chfieldvalue": "ON_QA",
        "classification": "Red Hat",
        "f3": "OP",
        "f6": "CP",
        "f7": "component",
        "o7": "notsubstring",
        "v7": "documentation",
        "j3": "OR",
        "product": BUGZILLA_PRODUCT,
        "query_format": "advanced",
        "target_release" : version,
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, [ON_QA, VERIFIED])
    return filter_only_bugs(bugs)


def get_qe_backlog(product=BUGZILLA_PRODUCT, target_version=VERSION):
    query = {
        "bug_status": "ON_QA",
        "classification" : "Red Hat",
        "query_format": "advanced",
        "product": product,
        "target_release": target_version,
        "include_fields": [
            "id",
            "status",
            "qa_contact",
            "severity"
        ],
    }
    bugs = bzapi.query(query)
    return bugs

def get_qe_backlog_by_component(product=BUGZILLA_PRODUCT, target_version=VERSION, component=""):
    query = {
        "bug_status": "ON_QA",
        "classification" : "Red Hat",
        "query_format": "advanced",
        "product": product,
        "component" : component,
        "target_release": target_version,
        "include_fields": [
            "id",
            "status",
            "qa_contact",
            "severity"
        ],
    }
    bugs = bzapi.query(query)
    return bugs


def get_bugs_per_member(
    member_name, product='', version='',
):
    query = {
        "bug_status": "ON_QA",
        "classification": "Red Hat",
        "product": product,
        "emailqa_contact1": "1",
        "emailtype1": "substring",
        "f2": "qa_contact",
        "include_fields": [
            "id",
            "status",
            "severity"
        ],
        "o2": "equals",
        "query_format": "advanced",
        "v2": f"{member_name}@redhat.com",
        "target_release": version,
    }
    bugs = bzapi.query(query)
    return bugs


def get_dev_backlog(product=BUGZILLA_PRODUCT, version=VERSION):
    query = {

        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV",
        "f3" : "OP",
        "f6" : "CP",
        "f7" : "component",
        "n7" : "1",
        "o7" : "equals",
        "product" : product,
        "query_format" : "advanced",
        "target_release" : version,
        "v7" : "Documentation",
        "include_fields": [
            "id",
            "status",
            "cf_pm_score",
            "summary",
            "status",
            "component",
            "severity",
            "creation_time",
            "keywords",
        ],
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST)
    return bugs

def get_dev_backlog_by_component(product=BUGZILLA_PRODUCT, target_version=VERSION, component=""):
    query = {
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV",
        "classification" : "Red Hat",
        "component" : component,
        "include_fields" : [
            "id",
            "status",
            "summary",
            "target_release",
            "severity",
            "qa_contact"
        ],
        "product" : product,
        "query_format" : "advanced",
        "target_release" : target_version
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST)
    return bugs

def get_critical_bugs():
    bugs = []
    query = {
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_QA",
        "classification" : "Red Hat",
        "f0" : "OP",
        "f1" : "bug_severity",
        "f2" : "CP",
        "o1" : "equals",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : VERSION,
        "v1" : "urgent",
        "include_fields": [
            "id",
            "status",
        ],
    }
    urgent_bugs = bzapi.query(query)
    bugs += filter_by_status(urgent_bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs


def get_regression_bugs_targeted():
    query = {
        "action" : "wrap",
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA",
        "classification" : "Red Hat",
        "f0" : "OP",
        "f2" : "keywords",
        "f3" : "CP",
        "j0" : "OR",
        "o2" : "substring",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : VERSION,
        "v2" : "Regression",
        "include_fields": [
            "id",
            "status",
        ],
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs

def get_regression_bugs():
    query = {
        "action" : "wrap",
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA",
        "classification" : "Red Hat",
        "f0" : "OP",
        "f2" : "keywords",
        "f3" : "CP",
        "j0" : "OR",
        "o2" : "substring",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "version" : VERSION,
        "v2" : "Regression",
        "include_fields": [
            "id",
            "status",
        ],
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs

def get_untriaged_bugs(version=VERSION):
    query = {
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA,VERIFIED,RELEASE_PENDING",
        "classification" : "Red Hat",
        "f1" : "flagtypes.name",
        "f2" : "flagtypes.name",
        "f3" : "flagtypes.name",
        "j_top" : "OR",
        "o1" : "notequals",
        "o2" : "notequals",
        "o3" : "notequals",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
        "v1" : "devel_ack+",
        "v2" : "pm_ack+",
        "v3" : "qa_ack+",
        "include_fields": [
            "id",
            "status",
        ],
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, [
        "NEW", "ASSIGNED", "POST", "MODIFIED", "ON_DEV", "ON_QA",
        "VERIFIED", "RELEASE_PENDING"
    ])
    return bugs


def get_doc_bugs():
    query = {
        "action" : "wrap",
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV",
        "classification" : "Red Hat",
        "component" : "Documentation",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : VERSION,
        "include_fields": [
            "id",
            "status",
        ],
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs


def get_performance_blockers():
    query = {
        "bug_status": "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA",
        "classification": "Red Hat",
        "f3": "OP",
        "f6": "CP",
        "j5": "OR",
        "keywords": "TestBlocker, Performance, ",
        "keywords_type": "allwords",
        "product": BUGZILLA_PRODUCT,
        "query_format": "advanced"
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs


def get_scale_blockers():
    query = {
        "bug_status": "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA",
        "classification": "Red Hat",
        "product": BUGZILLA_PRODUCT,
        "f3": "OP",
        "f6": "CP",
        "f7": "cf_qa_whiteboard",
        "keywords": "TestBlocker,",
        "keywords_type": "allwords",
        "o7": "substring",
        "query_format": "advanced",
        "v7": "Scale"
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs


def get_overall_backlog():
    query = {
        "action" : "wrap",
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA",
        "classification" : "Red Hat",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs

def get_overall_backlog_by_component(product=BUGZILLA_PRODUCT, component=""):
    query = {
        "action" : "wrap",
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA",
        "classification" : "Red Hat",
        "product" : product,
        "component" : component,
        "query_format" : "advanced",
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs


def get_all_bugs_in_version(version=VERSION):
    query = {
        "action" : "wrap",
        "classification" : "Red Hat",
        "f0" : "OP",
        "f2" : "CP",
        "f3" : "component",
        # "f4" : "component",
        "o3" : "notequals",
        # "o4" : "notequals",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "v3" : "Documentation",
        # "v4" : "Release",
        "version" : version,
        "include_fields": [
            "id",
            "status",
        ],
    }
    bugs = bzapi.query(query)
    return bugs


def get_all_bugs_targeted_to_version(version=VERSION):
    query = {
        "classification" : "Red Hat",
        "f0" : "OP",
        "f2" : "CP",
        "f3" : "component",
        "f4" : "component",
        "o3" : "notequals",
        "o4" : "notequals",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
         "v3" : "Documentation",
         "v4" : "Release",
         "include_fields": [
            "id",
            "status",
            "keywords"
        ],
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)


def get_all_regression_bugs(version=VERSION):
    query = {
        "action": "wrap",
        "bug_status": "__open__,__closed__",
        "f3": "OP",
        "f4": "product",
        "f6": "CP",
        "f7": "keywords",
        "j3": "OR",
        "o4": "equals",
        "o7": "anywordssubstr",
        "query_format": "advanced",
        "v4": BUGZILLA_PRODUCT,
        "v7": "Regression",
        "f8": "component",
        "o8": "notsubstring",
        "v8": "documentation",
        "version": version,
        "include_fields": [
            "id",
            "status",
            "keywords"
        ],

    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)


# def get_all_failedqa_bugs(version=VERSION):
#     query = {
#         "action": "wrap",
#         "bug_status": "__open__,__closed__",
#         "f3": "OP",
#         "f4": "product",
#         "f6": "CP",
#         "f7": "cf_verified",
#         "j3": "OR",
#         "o4": "equals",
#         "o7": "substring",
#         "query_format": "advanced",
#         "v4": BUGZILLA_PRODUCT,
#         "v7": "FailedQA",
#         "f8": "component",
#         "o8": "notsubstring",
#         "v8": "documentation",
#         "f9": "flagtypes.name",
#         "o9": "substring",
#         "v9": version,
#         "include_fields": [
#             "id",
#             "status",
#         ],
#     }
#     bugs = bzapi.query(query)
#     return bugs


def get_all_verified_bugs_closed(version=VERSION):
    query = {
        "bug_status" : "",
        "f1" : "bug_status",
        "f2" : "bug_status",
        "f3" : "bug_status",
        "o1" : "changedfrom",
        "o2" : "changedto",
        "o3" : "anywordssubstr",
        "product" : BUGZILLA_PRODUCT,
        "include_fields": [
            "id",
            "assigned_to",
            "status",
            "summary",
            "resolution",
            "keywords",
        ],
        "query_format" : "advanced",
        "target_release" : version,
        "v1" : "ON_QA",
        "v2" : "VERIFIED",
        "v3" : "VERIFIED RELEASE_PENDING CLOSED",
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)

def get_all_verified_bugs(version=VERSION):
    query = {
        "bug_status" : "",
        "f3" : "bug_status",
        "o3" : "anywordssubstr",
        "product" : BUGZILLA_PRODUCT,
        "include_fields": [
            "id",
            "assigned_to",
            "status",
            "summary",
            "resolution",
            "keywords",
        ],
        "query_format" : "advanced",
        "target_release" : version,
        "v3" : "VERIFIED",
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)    

def get_verified_bugs(
    version=VERSION, changed_from='-1w', changed_to='Now'
):
    query = {
        "bug_status" : "",
        "chfield" : "bug_status",
        "chfieldfrom": changed_from,
        "chfieldto": changed_to,
        "chfieldvalue" : "VERIFIED",
        "classification": "Red Hat",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
        "include_fields": [
            "id",
            "status",
        ],
    }
    bugs = bzapi.query(query)
    return bugs

def get_all_rejected_bugs(version=VERSION):
    query = {
        "bug_status" : "CLOSED",
        "f1" : "component",
        "f2" : "component",
        "o1" : "notequals",
        "o2" : "notequals",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "include_fields": [
            "id",
            "status",
            "resolution",
            "keywords",
        ],
        "v1" : "Documentation",
        "v2" : "Release",
        "version" : version
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)

def get_changed_bugs_in_the_past_x_time(time='-1h'):
    query = {
        "bug_status": "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,VERIFIED,ON_QA,RELEASE_PENDING",
        "classification": "Red Hat",
        "f3": "OP",
        "f6": "CP",
        "f9": "delta_ts",
        "j3": "OR",
        "o9": "greaterthan",
        "product": BUGZILLA_PRODUCT,
        "query_format": "advanced",
        "v9": time
    }

    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, [
        "NEW", "ASSIGNED", "POST", "MODIFIED", "ON_DEV", "VERIFIED", "ON_QA",
        "RELEASE_PENDING"
    ])
    return bugs


def get_quality_score(bug):
    qa_wb = bug.cf_qa_whiteboard
    if QUALITY_IMPACT in qa_wb:
        score_idx = int(qa_wb.find(QUALITY_IMPACT) + len(QUALITY_IMPACT))
        return int(qa_wb[score_idx:score_idx + 3])
    return -1

def get_num_of_closed_bugs_by_resolution_and_component(component, resolution, version=VERSION):
    query = {
        "bug_status" : "CLOSED",
        "component" : component,
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "resolution" : resolution,
        "version" : version
    }
    bugs = bzapi.query(query)
    return len(bugs)

def get_all_was_on_qa_bugs(version=VERSION):
    query = {
        "chfield" : "bug_status",
        "chfieldto" : "Now",
        "chfieldvalue" : "ON_QA",
        "classification" : "Red Hat",
        "f0" : "OP",
        "f2" : "CP",
        "f3" : "component",
        "f4" : "component",
        "o3" : "notequals",
        "o4" : "notequals",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "v3" : "Documentation",
        "v4" : "Release",
        "target_release" : version,
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)

def get_all_failedqa_bugs(version=VERSION):
    query = {
        "bug_status" : "",
        "f1" : "OP",
        "f10" : "bug_status",
        "f11" : "bug_status",
        "f12" : "CP",
        "f13" : "OP",
        "f14" : "bug_status",
        "f15" : "bug_status",
        "f16" : "CP",
        "f17" : "OP",
        "f18" : "bug_status",
        "f19" : "bug_status",
        "f2" : "bug_status",
        "f3" : "bug_status",
        "f4" : "CP",
        "f5" : "OP",
        "f6" : "bug_status",
        "f7" : "bug_status",
        "f8" : "CP",
        "f9" : "OP",
        "j1" : "AND_G",
        "j13" : "AND_G",
        "j17" : "AND_G",
        "j5" : "AND_G",
        "j9" : "AND_G",
        "j_top" : "OR",
        "o10" : "changedfrom",
        "o11" : "changedto",
        "o14" : "changedfrom",
        "o15" : "changedto",
        "o18" : "changedfrom",
        "o19" : "changedto",
        "o2" : "changedfrom",
        "o3" : "changedto",
        "o6" : "changedfrom",
        "o7" : "changedto",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
        "v10" : "ON_QA",
        "v11" : "MODIFIED",
        "v14" : "ON_QA",
        "v15" : "POST",
        "v18" : "ON_QA",
        "v19" : "ON_DEV",
        "v2" : "ON_QA",
        "v3" : "NEW",
        "v6" : "ON_QA",
        "v7" : "ASSIGNED"
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)

def get_all_reopened_bugs(version=VERSION):
    query = {
        "bug_status" : "",
        "f10" : "CP",
        "f11" : "OP",
        "f12" : "bug_status",
        "f13" : "bug_status",
        "f14" : "bug_status",
        "f4" : "OP",
        "f5" : "bug_status",
        "f6" : "bug_status",
        "f7" : "bug_status",
        "f8" : "bug_status",
        "f9" : "bug_status",
        "j11" : "OR",
        "j4" : "OR",
        "o12" : "changedfrom",
        "o13" : "changedfrom",
        "o14" : "changedfrom",
        "o5" : "changedto",
        "o6" : "changedto",
        "o7" : "changedto",
        "o8" : "changedto",
        "o9" : "changedto",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
        "v12" : "VERIFIED",
        "v13" : "RELEASE_PENDING",
        "v14" : "CLOSED",
        "v5" : "NEW",
        "v6" : "ASSIGNED",
        "v7" : "MODIFIED",
        "v8" : "POST",
        "v9" : "ON_QA"
    }
    bugs = bzapi.query(query)
    return filter_by_no_keywords(bugs, KEYWORD_FILTER)

def get_on_qa_bugs():
    query = BASE_QUERY.copy()
    query['bug_status'] = ON_QA
    bugs = bzapi.query(query)
    return filter_only_bugs(bugs)


def get_open_blockers():
    query = {     
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_QA",
        "f10" : "keywords",
        "f11" : "keywords",
        "f3" : "OP",
        "f6" : "CP",
        "f8" : "flagtypes.name",
        "j5" : "OR",
        "j_top" : "OR",
        "o10" : "substring",
        "o11" : "substring",
        "o8" : "anywordssubstr",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : VERSION,
        "v10" : "TestBlocker",
        "v11" : "AutomationBlocker",
        "v8" : "blocker+",
    }
    
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs

def get_open_candidate_blockers():
    query = {
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_QA",
        "f3" : "OP",
        "f6" : "CP",
        "f8" : "flagtypes.name",
        "j_top" : "OR",
        "o8" : "anywordssubstr",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : VERSION,
        "v8" : "blocker?"
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST)
    return bugs

def get_on_qa_blockers():
    query = BASE_QUERY.copy()
    query['bug_status'] = ON_QA
    query['v8'] = BLOCKER
    bugs = bzapi.query(query)
    return filter_only_bugs(bugs)


def get_deployment_blockers(version=VERSION):
    query = {
        "bug_status": "NEW,ASSIGNED,POST,MODIFIED",
        "f3": "OP",
        "f4": "product",
        "f6": "CP",
        "f7": "cf_qa_whiteboard",
        "j3": "OR",
        "o4": "equals",
        "o7": "anywordssubstr",
        "query_format": "advanced",
        "v4": BUGZILLA_PRODUCT,
        "v7": "Deployment_blocker",
        "f9": "flagtypes.name",
        "o9": "substring",
        "v9": version


    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST)
    return bugs


def get_feature_blockers(version=VERSION):
    query = {
        "bug_status": "NEW,ASSIGNED,POST,MODIFIED",
        "f3": "OP",
        "f4": "product",
        "f6": "CP",
        "f7": "cf_qa_whiteboard",
        "j3": "OR",
        "o4": "equals",
        "o7": "anywordssubstr",
        "query_format": "advanced",
        "v4": BUGZILLA_PRODUCT,
        "v7": "Feature_blocker",
        "f9": "flagtypes.name",
        "o9": "substring",
        "v9": version

    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST)
    return bugs


def get_stability_bugs(version=VERSION):
    query = {
        "bug_status": "NEW,ASSIGNED,POST,MODIFIED",
        "f3": "OP",
        "f4": "product",
        "f6": "CP",
        "f7": "cf_qa_whiteboard",
        "j3": "OR",
        "o4": "equals",
        "o7": "anywordssubstr",
        "query_format": "advanced",
        "v4": BUGZILLA_PRODUCT,
        "v7": "Stability",
        "f9": "flagtypes.name",
        "o9": "substring",
        "v9": version

    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST)
    return bugs

def get_blockers_list(version=VERSION):
    query = {
        "bug_status" : "",
        "f1" : "bug_status",
        "f2" : "OP",
        "f3" : "flagtypes.name",
        "f4" : "keywords",
        "j2" : "OR",
        "o1" : "anywordssubstr",
        "o3" : "anywordssubstr",
        "o4" : "anywordssubstr",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
        "v1" : "NEW ASSIGNED POST MODIFIED ON_QA",
        "v3" : "blocker+ blocker?",
        "v4" : "TestBlocker AutomationBlocker",
        "include_fields" : [
            "id",
            "component",
            "status",
            "summary",
            "flags",
            "keywords"
        ],
    }
    bugs = bzapi.query(query)
    return bugs

def get_urgent_list(version=VERSION):
    query = {
        "bug_severity" : "urgent",
        "bug_status" : "",
        "f1" : "bug_status",
        "f2" : "OP",
        "f4" : "keywords",
        "j2" : "OR",
        "o1" : "anywordssubstr",
        "o4" : "nowordssubstr",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : version,
        "v1" : "NEW ASSIGNED POST MODIFIED ON_QA",
        "v4" : "FutureFeature, Improvement, ",
        "include_fields" : [
            "id",
            "component",
            "status",
            "summary",
            "flags",
            "keywords"
        ],
    }
    bugs = bzapi.query(query)
    return bugs

def get_gss_closed_loop(flag, status=""):
    query = {
        "bug_status": status,
        "classification": "Red Hat",
        "f3": "flagtypes.name",
        "include_fields": [
            "id",
            "status",
            "component",
            "severity",
            "keywords",
        ],
        "o3": "substring",
        "product": BUGZILLA_PRODUCT,
        "query_format": "advanced",
        "v3": flag
    }

    bugs = bzapi.query(query)
    return filter_only_bugs(bugs)

def get_untargeted_bugs():
    query = {
        "bug_status" : "NEW,ASSIGNED,POST,MODIFIED,ON_DEV,ON_QA,VERIFIED",
        "classification" : "Red Hat",
        "product" : BUGZILLA_PRODUCT,
        "query_format" : "advanced",
        "target_release" : "---"
    }
    bugs = bzapi.query(query)
    bugs = filter_by_status(bugs, OPEN_BUGS_LIST_WITH_QA)
    return bugs

def get_dependent_product_bugs(severity=""):
    query = {
        "bug_status" : "",
        "f1" : "bug_status",
        "f2" : "OP",
        "f3" : "dependent_products",
        "f4" : "component",
        "f5" : "status_whiteboard",
        "j2" : "OR",
        "o1" : "anywordssubstr",
        "o3" : "equals",
        "o4" : "equals",
        "o5" : "substring",
        "query_format" : "advanced",
        "v1" : "NEW ASSIGNED POST MODIFIED ON_DEV ON_QA",
        "v3" : "Container Native Virtualization (CNV)",
        "v4" : "Compute Resources - CNV",
        "v5" : "Telco:CNV"
    }
    if severity:
        query["bug_severity"] = severity
    bugs = bzapi.query(query)
    return bugs
