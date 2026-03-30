#!/usr/bin/env python3
"""Yandex Tracker CLI — OpenClaw skill wrapper around yandex_tracker_client."""

import argparse
import json
import os
import sys

try:
    from yandex_tracker_client import TrackerClient
    from yandex_tracker_client.exceptions import NotFound, TrackerClientError
except ImportError:
    print("Error: yandex_tracker_client not installed. Run: pip install yandex_tracker_client", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_client():
    """Create TrackerClient from environment variables."""
    token = os.environ.get("YANDEX_TRACKER_TOKEN")
    iam_token = os.environ.get("YANDEX_TRACKER_IAM_TOKEN")
    org_id = os.environ.get("YANDEX_TRACKER_ORG_ID")
    cloud_org_id = os.environ.get("YANDEX_TRACKER_CLOUD_ORG_ID")
    base_url = os.environ.get("YANDEX_TRACKER_BASE_URL", "https://api.tracker.yandex.net")

    if not token and not iam_token:
        print("Error: Set YANDEX_TRACKER_TOKEN or YANDEX_TRACKER_IAM_TOKEN", file=sys.stderr)
        sys.exit(1)
    if not org_id and not cloud_org_id:
        print("Error: Set YANDEX_TRACKER_ORG_ID or YANDEX_TRACKER_CLOUD_ORG_ID", file=sys.stderr)
        sys.exit(1)

    kwargs = {"base_url": base_url}
    if iam_token:
        kwargs["iam_token"] = iam_token
        kwargs["cloud_org_id"] = cloud_org_id
    else:
        kwargs["token"] = token
        if cloud_org_id:
            kwargs["cloud_org_id"] = cloud_org_id
        else:
            kwargs["org_id"] = org_id

    return TrackerClient(**kwargs)


def obj_to_dict(obj):
    """Convert tracker object to serializable dict."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: obj_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [obj_to_dict(i) for i in obj]
    # Resource/Reference objects
    if hasattr(obj, "_value"):
        return obj_to_dict(obj._value)
    if hasattr(obj, "__dict__"):
        return {k: obj_to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return str(obj)


def output(data, fmt="json"):
    """Print data in requested format."""
    d = obj_to_dict(data)
    if fmt == "text":
        if isinstance(d, list):
            for item in d:
                if isinstance(item, dict):
                    print(" | ".join(f"{k}={v}" for k, v in item.items()))
                else:
                    print(item)
        elif isinstance(d, dict):
            for k, v in d.items():
                print(f"{k}: {v}")
        else:
            print(d)
    else:
        print(json.dumps(d, ensure_ascii=False, indent=2, default=str))


def parse_key_value_pairs(pairs):
    """Parse key=value pairs from CLI args into a dict."""
    result = {}
    if not pairs:
        return result
    for pair in pairs:
        if "=" not in pair:
            print(f"Error: Invalid key=value pair: {pair}", file=sys.stderr)
            sys.exit(1)
        key, value = pair.split("=", 1)
        # Try to parse JSON values (for nested objects like type={'name': 'Bug'})
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        result[key] = value
    return result


# ---------------------------------------------------------------------------
# Issue commands
# ---------------------------------------------------------------------------

def cmd_issue_get(args):
    client = get_client()
    try:
        issue = client.issues[args.key]
        output(issue, args.format)
    except NotFound:
        print(f"Issue {args.key} not found", file=sys.stderr)
        sys.exit(1)


def cmd_issue_create(args):
    client = get_client()
    kwargs = {"queue": args.queue, "summary": args.summary}
    if args.type:
        kwargs["type"] = {"name": args.type}
    if args.description:
        kwargs["description"] = args.description
    if args.assignee:
        kwargs["assignee"] = args.assignee
    if args.priority:
        kwargs["priority"] = args.priority
    if args.parent:
        kwargs["parent"] = args.parent
    if args.followers:
        kwargs["followers"] = args.followers
    extra = parse_key_value_pairs(args.field)
    kwargs.update(extra)
    issue = client.issues.create(**kwargs)
    output(issue, args.format)


def cmd_issue_update(args):
    client = get_client()
    issue = client.issues[args.key]
    kwargs = parse_key_value_pairs(args.field)
    if args.summary:
        kwargs["summary"] = args.summary
    if args.description:
        kwargs["description"] = args.description
    if args.assignee:
        kwargs["assignee"] = args.assignee
    if args.priority:
        kwargs["priority"] = args.priority
    if not kwargs:
        print("Error: No fields to update. Use --summary, --description, --assignee, --priority, or --field key=value", file=sys.stderr)
        sys.exit(1)
    issue.update(**kwargs)
    output(issue, args.format)


def cmd_issue_search(args):
    client = get_client()
    kwargs = {}
    if args.query:
        kwargs["query"] = args.query
    if args.filter:
        kwargs["filter"] = parse_key_value_pairs(args.filter)
    if args.per_page:
        kwargs["per_page"] = args.per_page
    if args.order:
        kwargs["order"] = args.order
    if args.keys:
        kwargs["keys"] = args.keys
    issues = client.issues.find(**kwargs)
    result = list(issues)
    output(result, args.format)


def cmd_issue_count(args):
    client = get_client()
    kwargs = {}
    if args.query:
        kwargs["query"] = args.query
    if args.filter:
        kwargs["filter"] = parse_key_value_pairs(args.filter)
    kwargs["count_only"] = True
    count = client.issues.find(**kwargs)
    print(count)


def cmd_issue_transitions(args):
    client = get_client()
    issue = client.issues[args.key]
    transitions = issue.transitions.get_all()
    output(list(transitions), args.format)


def cmd_issue_transition(args):
    client = get_client()
    issue = client.issues[args.key]
    transition = issue.transitions[args.transition]
    kwargs = {}
    if args.comment:
        kwargs["comment"] = args.comment
    if args.resolution:
        kwargs["resolution"] = args.resolution
    extra = parse_key_value_pairs(args.field)
    kwargs.update(extra)
    transition.execute(**kwargs)
    # Refresh issue
    issue = client.issues[args.key]
    output(issue, args.format)


def cmd_issue_move(args):
    client = get_client()
    issue = client.issues[args.key]
    issue.move_to(args.queue)
    issue = client.issues[args.key]
    output(issue, args.format)


def cmd_issue_clone(args):
    client = get_client()
    issue = client.issues[args.key]
    cloned = issue.clone_to(
        queues=args.queue,
        clone_all_fields=args.all_fields,
        link_with_original=args.link,
    )
    output(cloned, args.format)


def cmd_issue_changelog(args):
    client = get_client()
    issue = client.issues[args.key]
    changelog = list(issue.changelog)
    output(changelog, args.format)


# ---------------------------------------------------------------------------
# Comment commands
# ---------------------------------------------------------------------------

def cmd_comment_list(args):
    client = get_client()
    issue = client.issues[args.key]
    comments = list(issue.comments.get_all())
    output(comments, args.format)


def cmd_comment_create(args):
    client = get_client()
    issue = client.issues[args.key]
    kwargs = {"text": args.text}
    if args.attachments:
        kwargs["attachments"] = args.attachments
    comment = issue.comments.create(**kwargs)
    output(comment, args.format)


def cmd_comment_update(args):
    client = get_client()
    issue = client.issues[args.key]
    comment = issue.comments[int(args.comment_id)]
    comment.update(text=args.text)
    output(comment, args.format)


def cmd_comment_delete(args):
    client = get_client()
    issue = client.issues[args.key]
    comment = issue.comments[int(args.comment_id)]
    comment.delete()
    print(f"Comment {args.comment_id} deleted")


# ---------------------------------------------------------------------------
# Attachment commands
# ---------------------------------------------------------------------------

def cmd_attachment_list(args):
    client = get_client()
    issue = client.issues[args.key]
    attachments = list(issue.attachments)
    output(attachments, args.format)


def cmd_attachment_upload(args):
    client = get_client()
    issue = client.issues[args.key]
    attachment = issue.attachments.create(args.file)
    output(attachment, args.format)


def cmd_attachment_download(args):
    client = get_client()
    issue = client.issues[args.key]
    dest = args.dest or "."
    for attach in issue.attachments:
        if attach.name == args.filename or str(attach.id) == args.filename:
            attach.download_to(dest)
            print(f"Downloaded {attach.name} to {dest}")
            return
    print(f"Attachment '{args.filename}' not found", file=sys.stderr)
    sys.exit(1)


def cmd_attachment_delete(args):
    client = get_client()
    issue = client.issues[args.key]
    for attach in issue.attachments:
        if attach.name == args.filename or str(attach.id) == args.filename:
            attach.delete()
            print(f"Attachment '{args.filename}' deleted")
            return
    print(f"Attachment '{args.filename}' not found", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Link commands
# ---------------------------------------------------------------------------

def cmd_link_list(args):
    client = get_client()
    issue = client.issues[args.key]
    links = list(issue.links)
    output(links, args.format)


def cmd_link_create(args):
    client = get_client()
    issue = client.issues[args.key]
    link = issue.links.create(issue=args.target, relationship=args.relationship)
    output(link, args.format)


def cmd_link_delete(args):
    client = get_client()
    issue = client.issues[args.key]
    link = issue.links[int(args.link_id)]
    link.delete()
    print(f"Link {args.link_id} deleted")


def cmd_remotelink_create(args):
    client = get_client()
    issue = client.issues[args.key]
    link = issue.remotelinks.create(
        origin=args.origin,
        key=args.remote_key,
        relationship=args.relationship,
    )
    output(link, args.format)


# ---------------------------------------------------------------------------
# Queue commands
# ---------------------------------------------------------------------------

def cmd_queue_get(args):
    client = get_client()
    queue = client.queues[args.key]
    output(queue, args.format)


def cmd_queue_list(args):
    client = get_client()
    queues = list(client.queues.get_all())
    if args.limit:
        queues = queues[:args.limit]
    output(queues, args.format)


# ---------------------------------------------------------------------------
# Bulk commands
# ---------------------------------------------------------------------------

def cmd_bulk_update(args):
    client = get_client()
    kwargs = parse_key_value_pairs(args.field)
    bulkchange = client.bulkchange.update(args.issues, **kwargs)
    if args.wait:
        bulkchange = bulkchange.wait()
    output(bulkchange, args.format)


def cmd_bulk_transition(args):
    client = get_client()
    kwargs = parse_key_value_pairs(args.field)
    bulkchange = client.bulkchange.transition(args.issues, args.transition, **kwargs)
    if args.wait:
        bulkchange = bulkchange.wait()
    output(bulkchange, args.format)


def cmd_bulk_move(args):
    client = get_client()
    bulkchange = client.bulkchange.move(args.issues, args.queue)
    if args.wait:
        bulkchange = bulkchange.wait()
    output(bulkchange, args.format)


# ---------------------------------------------------------------------------
# Worklog commands
# ---------------------------------------------------------------------------

def cmd_worklog_list(args):
    client = get_client()
    issue = client.issues[args.key]
    worklogs = list(issue.worklog)
    output(worklogs, args.format)


def cmd_worklog_create(args):
    client = get_client()
    issue = client.issues[args.key]
    kwargs = {"start": args.start, "duration": args.duration}
    if args.comment:
        kwargs["comment"] = args.comment
    worklog = issue.worklog.create(**kwargs)
    output(worklog, args.format)


# ---------------------------------------------------------------------------
# Checklist commands
# ---------------------------------------------------------------------------

def cmd_checklist_list(args):
    client = get_client()
    issue = client.issues[args.key]
    items = list(issue.checklist_items)
    output(items, args.format)


def cmd_checklist_add(args):
    client = get_client()
    issue = client.issues[args.key]
    kwargs = {"text": args.text}
    if args.assignee:
        kwargs["assignee"] = args.assignee
    if args.deadline:
        kwargs["deadline"] = args.deadline
    issue.add_checklist_item(**kwargs)
    print(f"Checklist item added to {args.key}")


# ---------------------------------------------------------------------------
# User / info commands
# ---------------------------------------------------------------------------

def cmd_myself(args):
    client = get_client()
    me = client.myself
    output(me, args.format)


def cmd_user_get(args):
    client = get_client()
    user = client.users[args.uid]
    output(user, args.format)


# ---------------------------------------------------------------------------
# Board / Sprint commands
# ---------------------------------------------------------------------------

def cmd_board_list(args):
    client = get_client()
    boards = list(client.boards.get_all())
    output(boards, args.format)


def cmd_board_get(args):
    client = get_client()
    board = client.boards[args.board_id]
    output(board, args.format)


def cmd_sprint_list(args):
    client = get_client()
    board = client.boards[args.board_id]
    sprints = list(board.sprints)
    output(sprints, args.format)


# ---------------------------------------------------------------------------
# Version commands
# ---------------------------------------------------------------------------

def cmd_version_list(args):
    client = get_client()
    versions = list(client.versions.get_all())
    output(versions, args.format)


def cmd_version_get(args):
    client = get_client()
    version = client.versions[args.version_id]
    output(version, args.format)


# ---------------------------------------------------------------------------
# Component commands
# ---------------------------------------------------------------------------

def cmd_component_list(args):
    client = get_client()
    components = list(client.components.get_all())
    output(components, args.format)


# ---------------------------------------------------------------------------
# Field commands
# ---------------------------------------------------------------------------

def cmd_field_list(args):
    client = get_client()
    fields = list(client.fields.get_all())
    output(fields, args.format)


# ---------------------------------------------------------------------------
# Filter commands
# ---------------------------------------------------------------------------

def cmd_filter_list(args):
    client = get_client()
    filters = list(client.filters.get_all())
    output(filters, args.format)


def cmd_filter_get(args):
    client = get_client()
    f = client.filters[args.filter_id]
    output(f, args.format)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Yandex Tracker CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json",
                        help="Output format (default: json)")

    sub = parser.add_subparsers(dest="command", help="Command group")

    # --- issue ---
    issue_p = sub.add_parser("issue", help="Issue operations")
    issue_sub = issue_p.add_subparsers(dest="action")

    # issue get
    p = issue_sub.add_parser("get", help="Get issue by key")
    p.add_argument("key", help="Issue key (e.g. QUEUE-42)")

    # issue create
    p = issue_sub.add_parser("create", help="Create issue")
    p.add_argument("--queue", "-q", required=True)
    p.add_argument("--summary", "-s", required=True)
    p.add_argument("--type", "-t", default=None)
    p.add_argument("--description", "-d", default=None)
    p.add_argument("--assignee", default=None)
    p.add_argument("--priority", default=None)
    p.add_argument("--parent", default=None)
    p.add_argument("--followers", nargs="*", default=None)
    p.add_argument("--field", nargs="*", help="Extra fields as key=value")

    # issue update
    p = issue_sub.add_parser("update", help="Update issue")
    p.add_argument("key", help="Issue key")
    p.add_argument("--summary", default=None)
    p.add_argument("--description", default=None)
    p.add_argument("--assignee", default=None)
    p.add_argument("--priority", default=None)
    p.add_argument("--field", nargs="*", help="Extra fields as key=value")

    # issue search
    p = issue_sub.add_parser("search", help="Search issues")
    p.add_argument("--query", default=None, help="Query string (tracker QL)")
    p.add_argument("--filter", nargs="*", help="Filter as key=value pairs")
    p.add_argument("--per-page", type=int, default=None)
    p.add_argument("--order", nargs="*", default=None, help="Order fields (e.g. -status +priority)")
    p.add_argument("--keys", nargs="*", default=None, help="Specific issue keys")

    # issue count
    p = issue_sub.add_parser("count", help="Count issues matching query")
    p.add_argument("--query", default=None)
    p.add_argument("--filter", nargs="*", help="Filter as key=value pairs")

    # issue transitions
    p = issue_sub.add_parser("transitions", help="List available transitions")
    p.add_argument("key", help="Issue key")

    # issue transition
    p = issue_sub.add_parser("transition", help="Execute transition")
    p.add_argument("key", help="Issue key")
    p.add_argument("transition", help="Transition ID")
    p.add_argument("--comment", default=None)
    p.add_argument("--resolution", default=None)
    p.add_argument("--field", nargs="*", help="Extra fields as key=value")

    # issue move
    p = issue_sub.add_parser("move", help="Move issue to another queue")
    p.add_argument("key", help="Issue key")
    p.add_argument("queue", help="Target queue key")

    # issue clone
    p = issue_sub.add_parser("clone", help="Clone issue")
    p.add_argument("key", help="Issue key")
    p.add_argument("queue", help="Target queue key")
    p.add_argument("--all-fields", action="store_true", help="Clone all fields")
    p.add_argument("--link", action="store_true", help="Link with original")

    # issue changelog
    p = issue_sub.add_parser("changelog", help="Issue changelog")
    p.add_argument("key", help="Issue key")

    # --- comment ---
    comment_p = sub.add_parser("comment", help="Comment operations")
    comment_sub = comment_p.add_subparsers(dest="action")

    p = comment_sub.add_parser("list", help="List comments")
    p.add_argument("key", help="Issue key")

    p = comment_sub.add_parser("create", help="Add comment")
    p.add_argument("key", help="Issue key")
    p.add_argument("--text", "-t", required=True)
    p.add_argument("--attachments", nargs="*", default=None, help="File paths to attach")

    p = comment_sub.add_parser("update", help="Update comment")
    p.add_argument("key", help="Issue key")
    p.add_argument("comment_id", help="Comment ID")
    p.add_argument("--text", "-t", required=True)

    p = comment_sub.add_parser("delete", help="Delete comment")
    p.add_argument("key", help="Issue key")
    p.add_argument("comment_id", help="Comment ID")

    # --- attachment ---
    attach_p = sub.add_parser("attachment", help="Attachment operations")
    attach_sub = attach_p.add_subparsers(dest="action")

    p = attach_sub.add_parser("list", help="List attachments")
    p.add_argument("key", help="Issue key")

    p = attach_sub.add_parser("upload", help="Upload attachment")
    p.add_argument("key", help="Issue key")
    p.add_argument("file", help="File path")

    p = attach_sub.add_parser("download", help="Download attachment")
    p.add_argument("key", help="Issue key")
    p.add_argument("filename", help="Attachment name or ID")
    p.add_argument("--dest", default=None, help="Destination directory")

    p = attach_sub.add_parser("delete", help="Delete attachment")
    p.add_argument("key", help="Issue key")
    p.add_argument("filename", help="Attachment name or ID")

    # --- link ---
    link_p = sub.add_parser("link", help="Link operations")
    link_sub = link_p.add_subparsers(dest="action")

    p = link_sub.add_parser("list", help="List links")
    p.add_argument("key", help="Issue key")

    p = link_sub.add_parser("create", help="Create link")
    p.add_argument("key", help="Issue key")
    p.add_argument("target", help="Target issue key")
    p.add_argument("--relationship", "-r", default="relates",
                   help="Relationship type (default: relates)")

    p = link_sub.add_parser("delete", help="Delete link")
    p.add_argument("key", help="Issue key")
    p.add_argument("link_id", help="Link ID")

    p = link_sub.add_parser("remote-create", help="Create remote link")
    p.add_argument("key", help="Issue key")
    p.add_argument("--origin", required=True)
    p.add_argument("--remote-key", required=True)
    p.add_argument("--relationship", "-r", default="relates")

    # --- queue ---
    queue_p = sub.add_parser("queue", help="Queue operations")
    queue_sub = queue_p.add_subparsers(dest="action")

    p = queue_sub.add_parser("get", help="Get queue info")
    p.add_argument("key", help="Queue key")

    p = queue_sub.add_parser("list", help="List queues")
    p.add_argument("--limit", type=int, default=None)

    # --- bulk ---
    bulk_p = sub.add_parser("bulk", help="Bulk operations")
    bulk_sub = bulk_p.add_subparsers(dest="action")

    p = bulk_sub.add_parser("update", help="Bulk update issues")
    p.add_argument("issues", nargs="+", help="Issue keys")
    p.add_argument("--field", nargs="*", required=True, help="Fields as key=value")
    p.add_argument("--wait", action="store_true", help="Wait for completion")

    p = bulk_sub.add_parser("transition", help="Bulk transition")
    p.add_argument("issues", nargs="+", help="Issue keys")
    p.add_argument("--transition", "-t", required=True, help="Transition ID")
    p.add_argument("--field", nargs="*", help="Extra fields as key=value")
    p.add_argument("--wait", action="store_true", help="Wait for completion")

    p = bulk_sub.add_parser("move", help="Bulk move issues")
    p.add_argument("issues", nargs="+", help="Issue keys")
    p.add_argument("--queue", "-q", required=True, help="Target queue")
    p.add_argument("--wait", action="store_true", help="Wait for completion")

    # --- worklog ---
    worklog_p = sub.add_parser("worklog", help="Worklog operations")
    worklog_sub = worklog_p.add_subparsers(dest="action")

    p = worklog_sub.add_parser("list", help="List worklog entries")
    p.add_argument("key", help="Issue key")

    p = worklog_sub.add_parser("create", help="Add worklog entry")
    p.add_argument("key", help="Issue key")
    p.add_argument("--start", required=True, help="Start datetime (ISO 8601)")
    p.add_argument("--duration", required=True, help="Duration (e.g. P1DT2H3M)")
    p.add_argument("--comment", default=None)

    # --- checklist ---
    checklist_p = sub.add_parser("checklist", help="Checklist operations")
    checklist_sub = checklist_p.add_subparsers(dest="action")

    p = checklist_sub.add_parser("list", help="List checklist items")
    p.add_argument("key", help="Issue key")

    p = checklist_sub.add_parser("add", help="Add checklist item")
    p.add_argument("key", help="Issue key")
    p.add_argument("--text", "-t", required=True)
    p.add_argument("--assignee", default=None)
    p.add_argument("--deadline", default=None)

    # --- user ---
    user_p = sub.add_parser("user", help="User operations")
    user_sub = user_p.add_subparsers(dest="action")

    p = user_sub.add_parser("me", help="Current user info")

    p = user_sub.add_parser("get", help="Get user by uid/login")
    p.add_argument("uid", help="User ID or login")

    # --- board ---
    board_p = sub.add_parser("board", help="Board operations")
    board_sub = board_p.add_subparsers(dest="action")

    p = board_sub.add_parser("list", help="List boards")
    p = board_sub.add_parser("get", help="Get board")
    p.add_argument("board_id", help="Board ID")

    p = board_sub.add_parser("sprints", help="List sprints for board")
    p.add_argument("board_id", help="Board ID")

    # --- version ---
    version_p = sub.add_parser("version", help="Version operations")
    version_sub = version_p.add_subparsers(dest="action")

    p = version_sub.add_parser("list", help="List versions")
    p = version_sub.add_parser("get", help="Get version")
    p.add_argument("version_id", help="Version ID")

    # --- component ---
    component_p = sub.add_parser("component", help="Component operations")
    component_sub = component_p.add_subparsers(dest="action")

    p = component_sub.add_parser("list", help="List components")

    # --- field ---
    field_p = sub.add_parser("field", help="Field operations")
    field_sub = field_p.add_subparsers(dest="action")

    p = field_sub.add_parser("list", help="List fields")

    # --- filter ---
    filter_p = sub.add_parser("filter", help="Filter operations")
    filter_sub = filter_p.add_subparsers(dest="action")

    p = filter_sub.add_parser("list", help="List saved filters")
    p = filter_sub.add_parser("get", help="Get filter")
    p.add_argument("filter_id", help="Filter ID")

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

DISPATCH = {
    ("issue", "get"): cmd_issue_get,
    ("issue", "create"): cmd_issue_create,
    ("issue", "update"): cmd_issue_update,
    ("issue", "search"): cmd_issue_search,
    ("issue", "count"): cmd_issue_count,
    ("issue", "transitions"): cmd_issue_transitions,
    ("issue", "transition"): cmd_issue_transition,
    ("issue", "move"): cmd_issue_move,
    ("issue", "clone"): cmd_issue_clone,
    ("issue", "changelog"): cmd_issue_changelog,
    ("comment", "list"): cmd_comment_list,
    ("comment", "create"): cmd_comment_create,
    ("comment", "update"): cmd_comment_update,
    ("comment", "delete"): cmd_comment_delete,
    ("attachment", "list"): cmd_attachment_list,
    ("attachment", "upload"): cmd_attachment_upload,
    ("attachment", "download"): cmd_attachment_download,
    ("attachment", "delete"): cmd_attachment_delete,
    ("link", "list"): cmd_link_list,
    ("link", "create"): cmd_link_create,
    ("link", "delete"): cmd_link_delete,
    ("link", "remote-create"): cmd_remotelink_create,
    ("queue", "get"): cmd_queue_get,
    ("queue", "list"): cmd_queue_list,
    ("bulk", "update"): cmd_bulk_update,
    ("bulk", "transition"): cmd_bulk_transition,
    ("bulk", "move"): cmd_bulk_move,
    ("worklog", "list"): cmd_worklog_list,
    ("worklog", "create"): cmd_worklog_create,
    ("checklist", "list"): cmd_checklist_list,
    ("checklist", "add"): cmd_checklist_add,
    ("user", "me"): cmd_myself,
    ("user", "get"): cmd_user_get,
    ("board", "list"): cmd_board_list,
    ("board", "get"): cmd_board_get,
    ("board", "sprints"): cmd_sprint_list,
    ("version", "list"): cmd_version_list,
    ("version", "get"): cmd_version_get,
    ("component", "list"): cmd_component_list,
    ("field", "list"): cmd_field_list,
    ("filter", "list"): cmd_filter_list,
    ("filter", "get"): cmd_filter_get,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    key = (args.command, getattr(args, "action", None))
    handler = DISPATCH.get(key)

    if handler is None:
        # Try subparser help
        parser.parse_args([args.command, "--help"])
        sys.exit(1)

    try:
        handler(args)
    except TrackerClientError as e:
        print(f"Tracker error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
