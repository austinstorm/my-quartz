import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { FullSlug, resolveRelative } from "../util/path"
import { classNames } from "../util/lang"

interface Options {
  title?: string
  limit?: number
  sort?: "count" | "alphabetical"
  showCounts?: boolean
}

const defaultOptions: Options = {
  title: "Top Tags",
  limit: 30,
  sort: "count",
  showCounts: true,
}

export default ((userOpts?: Partial<Options>) => {
  const TagNav: QuartzComponent = ({
    allFiles,
    fileData,
    displayClass,
  }: QuartzComponentProps) => {
    const opts = { ...defaultOptions, ...userOpts }

    const counts = new Map<string, number>()
    for (const file of allFiles) {
      for (const tag of file.frontmatter?.tags ?? []) {
        counts.set(tag, (counts.get(tag) ?? 0) + 1)
      }
    }

    let tags = [...counts.keys()]
    if (opts.sort === "count") {
      tags.sort((a, b) => (counts.get(b) ?? 0) - (counts.get(a) ?? 0))
    } else {
      tags.sort()
    }
    if (opts.limit) {
      tags = tags.slice(0, opts.limit)
    }

    return (
      <div class={classNames(displayClass, "tag-nav")}>
        <h3>{opts.title}</h3>
        <ul>
          {tags.map((tag) => (
            <li>
              <a
                class="internal"
                href={resolveRelative(fileData.slug!, `tags/${tag}` as FullSlug)}
              >
                {tag}
              </a>
              {opts.showCounts && <span class="tag-count">{counts.get(tag)}</span>}
            </li>
          ))}
        </ul>
      </div>
    )
  }

  TagNav.css = `
    .tag-nav h3 {
      margin: 0.5rem 0 0 0;
      font-size: 1rem;
    }
    .tag-nav ul {
      list-style: none;
      margin: 0.5rem 0 0 0;
      padding-left: 0;
    }
    .tag-nav li {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding: 0.15rem 0;
    }
    .tag-nav li > a {
      color: var(--dark);
      opacity: 0.75;
      background-color: transparent;
    }
    .tag-nav li > a:hover {
      color: var(--tertiary);
      opacity: 1;
    }
    .tag-nav .tag-count {
      color: var(--gray);
      font-size: 0.8rem;
      opacity: 0.7;
    }
  `

  return TagNav
}) satisfies QuartzComponentConstructor
