# Course Website

```{note}
This page is a placeholder for the **15-322 / 15-622** course website. It is kept
in the table of contents so course material lives alongside the textbook. Expand
it into its own part (syllabus, schedule, assignments, policies) when ready — see
the authoring notes below.
```

## Course at a glance

- **Course:** 15-322 / 15-622 Introduction to Computer Music
- **Institution:** Carnegie Mellon University
- **Semester:** TODO
- **Instructor:** TODO
- **Lectures:** TODO (time / location)
- **Office hours:** TODO

## Syllabus

TODO — course description, prerequisites, and learning objectives.

## Schedule

TODO — week-by-week topics, readings, and milestones.

| Week | Topic | Reading | Assignment |
| ---- | ----- | ------- | ---------- |
| 1    | TODO  | TODO    | TODO       |

## Assignments

TODO — list assignments with due dates and links.

## Policies

TODO — grading, late work, collaboration, and academic integrity.

---

### Authoring notes

To grow this into a full website, replace this single page with a part in
`_toc.yml`, for example:

```yaml
  - caption: Course Information
    numbered: false
    chapters:
      - file: content/course/intro
        sections:
          - file: content/course/syllabus
          - file: content/course/schedule
          - file: content/course/assignments
          - file: content/course/policies
```

Each entry is a Markdown (or notebook) file under `content/course/`.
```
