# Third-party notices and attribution

The harness implementation, synthetic fixtures, and regression checks in this
repository are maintained for the Commitment Issues hackathon project and are
licensed under the MIT License in [LICENSE](LICENSE).

Benchmark documentation and runner scripts describe or operate on separately
obtained upstream repositories, including [Fiber](https://github.com/gofiber/fiber)
and [Sequelize](https://github.com/sequelize/sequelize). Their source checkouts
and generated run targets are local benchmark inputs under ignored `artifacts/`
and are not included in this repository or its submission archive. The small
Fiber regression check and Sequelize compatibility check committed here were
written for this benchmark; they do not contain upstream implementation source.
When obtaining or redistributing an upstream checkout, follow that project's
license and retain its notices.

The Python package declares no third-party runtime dependencies. CI uses
GitHub-maintained `actions/checkout` and `actions/setup-python` actions by
reference in the workflow; their terms and notices are provided by their
respective publishers.
