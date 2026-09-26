package fiber

import (
	"testing"

	"github.com/stretchr/testify/require"
	"github.com/valyala/fasthttp"
)

// Empty list elements are ignored as ranges but count toward MaxRanges.
// The final empty element must count exactly like a leading empty element.
func Test_Harness_RangeMaxRanges(t *testing.T) {
	t.Parallel()
	cases := []struct {
		name     string
		header   string
		limit    int
		tooLarge bool
	}{
		{"trailing_one_over_limit", "bytes=0-0,", 1, true},
		{"trailing_two_over_limit", "bytes=0-0,,", 2, true},
		{"trailing_whitespace_over_limit", "bytes=0-0,, \t", 2, true},
		{"leading_empty_over_limit", "bytes=,,0-0", 2, true},
		{"trailing_empty_within_limit", "bytes=0-0,", 2, false},
		{"two_ranges_within_limit", "bytes=0-0,1-1", 2, false},
		{"single_range_at_limit", "bytes=0-0", 1, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			app := New(Config{MaxRanges: tc.limit})
			c := app.AcquireCtx(&fasthttp.RequestCtx{})
			defer app.ReleaseCtx(c)
			c.Request().Header.Set(HeaderRange, tc.header)
			result, err := c.Range(10)
			if tc.tooLarge {
				require.ErrorIs(t, err, ErrRangeTooLarge)
				require.Equal(t, StatusRequestedRangeNotSatisfiable, c.Response().StatusCode())
				require.Equal(t, "bytes */10", string(c.Response().Header.Peek(HeaderContentRange)))
			} else {
				require.NoError(t, err)
				require.NotEmpty(t, result.Ranges)
				require.Equal(t, RangeSet{Start: 0, End: 0}, result.Ranges[0])
			}
		})
	}
}
