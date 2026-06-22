# Projects

## List of released projects

- [Project 1](./1.md)
- [Project 2](./2.md)

## Submission instructions and policies

All projects in this course have an _autograded_ component, which will be submitted via a project-specific Gradescope link.

Most projects additionally have an _open-ended_ component, which will be checked with a [common Gradescope validation tool](https://www.gradescope.com/courses/1326756/assignments/8238316) and then [submitted via Google Forms](https://forms.gle/Q2fjknDhxNMsR24J7).

**Academic integrity**. **You cannot work with other students on projects.** All work must be your own. Some parts of projects will allow you to use AI tools. If you choose to use AI, **you remain responsible for _every bit_ of information in your project submissions.**

**Enforcement**. **We reserve the right at any time to give you an oral or written quiz on the details of your project submission.** These quizzes will be trivial if you completed your work appropriately, or difficult if you worked with other students or used AI inappropriately. E.g., "Which of these functions did your implementation call for task 4", or "Which of these sentences appeared in your project writeup". If you fail one of these quizzes, we will give you a 0 on the project, and could result in a report to the university for an academic integrity violation.

**Late work**. To get full credit, **you must upload your assignment to the correct portal by 11:59:00p Eastern Time on the day of the deadline**. See our [course syllabus](../syllabus.md) for the late submission policy and information on partial credit.

### Autograded submission instructions and policies

Autograded components of projects will be submitted via [Gradescope](https://www.gradescope.com/courses/1326756). Please see each project description for a link to the Gradescope submission portal specific to that project.

**You are _not_ allowed to use AI when completing autograded portions of course projects** (except in rare cases when specified in the project description, for example the last task of Project 1). See [above info](#submission-instructions-and-policies) for enforcement policies.

#### **Grading policy**

Your grade for the autograded section of each project will be calculated as:

- 70% autograded score (e.g., 14/15 on Gradescope is 65.3% points)
- 30% free text responses (manually graded by TAs)

### Open-ended submission instructions and policies

Open-ended project sections will be in one of two formats: _creative_, or _technical_. Projects will be submitted as bundled `.zip` files conforming to the format descriptions below, and must not exceed 100MB.

When you are ready to submit, validate your zip file with this [Gradescope validation tool](https://www.gradescope.com/courses/1326756/assignments/8238316) and then [submit via Google Forms](https://forms.gle/Q2fjknDhxNMsR24J7). You may update your Google Forms submission as many times as you like - we will use your last submission before the deadline.

**You _are_ allowed to use AI when completing open-ended portions of course projects.** If you use AI, you are expected to iterate closely with the AI system and retain the agency on high-level project directions and decisions. Regardless of if you use AI, **you are responsible for reading and verifying every bit of code and information submitted in your project zip file.**

#### **Creative format**

This format centers around creating a musical composition by combining a creative vision with technical computer music programming.

An ideal project involves a non-trivial amount of programming in Python/Pyquist to accomplish a focused creative goal that conforms to all stated requirements. External tools (e.g., DAWs like Ableton Live) are allowed, but significant portions of your composition should be realized in code.

Computer music does not have to sound like something you would hear on the radio! Grading will center around your technical achievments and realization of your creative intent, not the aesthetics of your composition.

**Submission files**

Place all of the following files in a single zip file:

1. `composition.wav` | `composition.mp3`: Your final composition audio file. Minimum 30s, maximum 5 minutes, 44.1kHz or 48kHz, stereo preferred. One of WAV or MP3 is required; WAV is preferred, but MP3 is acceptable if you're having trouble fitting into the 100MB limit.
1. `CREATIVE.md`: A [Markdown](https://www.markdownguide.org) file fully documenting your project, in the _exact_ format of the template below.
1. `src/`: A directory containing your Python/Pyquist code. A non-trivial portion of `composition.wav` must be generated when re-executing this Python code. Any structure is fine within this directory, as long sufficient documentation appears in `CREATIVE.md` (see below). Include all dependencies necessary to execute your code, including code dependencies and sound assets. Any dependency that we can `pip install` does _not_ need to be included.

**[Click here to download the template for `CREATIVE.md`](https://gclef-cmu.org/icm-autograde/projects-f26/open-ended/starter.zip)**. Your `CREATIVE.md` file should be formatted exactly like this template. Namely, all `## Section Headings` should remain unchanged, but otherwise all text below should be replaced with your own writing.

#### **Technical format**

This format centers around accomplishing an ambitious technical computer music programming goal, and documenting your accomplishments with a video demonstration.

An ideal project involves accomplishing an ambitious technical goal and conforming to all stated requirements. Degree of ambition expected will vary with the amount of self-reported AI coding assistance (more AI = higher expectaitons, less AI = lower expectations).

Your video presentation _must_ adhere to the following format:

- Between 60s and 180s in length
- Must be **narrated with your own voice**
- Screen recording preferred (Zoom, OBS), cell phone videos of screens accepted assuming we can see your screen clearly
  - Easy screen recording: Start a Zoom meeting. Click Share screen and **make sure _Share sound_ is enabled**. Click More > Record > Record to this computer
- Presentation flow w/ suggested durations:
  - (10-20s) State the high-level goal of your project
  - (15-60s) Show a demo of your final result
  - (30-60s) Explain how you satisfied each project requirement
  - (00-60s) Share any additional technical accomplishments or features of your demo that you'd like to highlight
- Acceptable visuals: code, slides, demos, anything really (keep it appropriate)

Use `ffmpeg` to reduce file size, e.g.:

```sh
ffmpeg -i demo.mov -vcodec libx264 -crf 28 demo.mp4
```

**Submission files**

Place all of the following files in a single zip file:

1. `demo.mp4` | `demo.mov` | `demo.mkv`: Your final demo video file. Minimum 1m, maximum 3m. Your video must adhere to the guidelines above.
1. `TECHNICAL.md`: A [Markdown](https://www.markdownguide.org) file fully documenting your project, in the _exact_ format of the template below.
1. `src/`: A directory containing your Python/Pyquist code. Any structure is fine within this directory, as long sufficient documentation appears in `TECHNICAL.md` (see below). Include all dependencies necessary to execute your code, including code dependencies and sound assets. Any dependency that we can `pip install` does _not_ need to be included.

**[Click here to download the template for `TECHNICAL.md`](https://gclef-cmu.org/icm-autograde/projects-f26/open-ended/starter.zip)**. Your `TECHNICAL.md` file should be formatted exactly like this template. Namely, all `## Section Headings` should remain unchanged, but otherwise all text below should be replaced with your own writing.

#### **Grading policy**

Your grade for the autograded section of each project will be calculated as:

- 20% passes formatting checks on Gradescope
- 80% manual grading by TAs, following the rubric below

**Rubric**

TODO...
