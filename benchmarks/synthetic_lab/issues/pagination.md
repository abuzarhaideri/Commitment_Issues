Pagination skips the first page and returns incorrect later pages.
The page number is one-based and page_size is the number of items per page.
For positive integer arguments, return the requested slice, including a partial
last page; empty input and pages beyond the end return an empty list.
Reject page < 1 or page_size < 1 with ValueError. Do not mutate the input list.
Preserve other modules and the public signature. Do not modify tests.
