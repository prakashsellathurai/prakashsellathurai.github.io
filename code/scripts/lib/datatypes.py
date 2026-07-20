from typing import TypedDict, NotRequired


class Essay(TypedDict):
    slug: str
    title: str
    date: str
    summary: str
    tags: list[str]
    content: str


class Note(TypedDict):
    title: str
    slug: str
    content: str


class FileData(TypedDict):
    filename: str
    slug: str
    title: str
    ext: str
    content: str


class Subtopic(TypedDict):
    subtopic_path: str
    subtopic_title: str
    files: list[FileData]


class ExperimentTopic(TypedDict):
    topic: str
    topic_slug: str
    topic_title: str
    files: list[FileData]
    subtopics: list[Subtopic]


class Project(TypedDict):
    title: str
    href: str
    website: NotRequired[str]
    description: str
    stars: int
    tags: NotRequired[list[str]]


class Book(TypedDict):
    title: str
    author: str
    link: str
    imageUrl: str
    imageUrlRemote: NotRequired[str]
    rating: NotRequired[int]


class Quote(TypedDict):
    quote: str
    author: NotRequired[str]
    book: NotRequired[str]
    url: NotRequired[str]


class LeetcodeSolution(TypedDict):
    href: str
    title: NotRequired[str]


class SiteMetadata(TypedDict):
    title: str
    description: str
    siteUrl: str
    author: str
    authorDetails: NotRequired[dict]
    socialBanner: NotRequired[str]
    siteLogo: NotRequired[str]
    keywords: NotRequired[list[str]]
    language: NotRequired[str]
    email: NotRequired[str]
