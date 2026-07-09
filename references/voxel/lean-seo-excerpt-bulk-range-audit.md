# Klarc bulk excerpt range audit pattern

Session pattern: user asked to set proper excerpts on every page and CPT and find all excerpts outside Google best-practice range.

Useful workflow:

1. List public post types:
   ```bash
   wp post-type list --public=1 --fields=name,label --format=csv
   ```
2. Choose real content types only. For Klarc, used:
   `post,page,events,exp,geo,glossaire,testimonials`.
   Skipped `attachment`, `elementor_library`, `e-floating-buttons`.
3. First audit via SQL, not full JSON, to avoid control-character JSON failures:
   ```sql
   SELECT post_type, COUNT(*) total,
          SUM(CHAR_LENGTH(TRIM(post_excerpt))<120 OR CHAR_LENGTH(TRIM(post_excerpt))>160) bad,
          MIN(CHAR_LENGTH(TRIM(post_excerpt))) min_len,
          MAX(CHAR_LENGTH(TRIM(post_excerpt))) max_len
   FROM wp_posts
   WHERE post_status='publish'
     AND post_type IN ('post','page','events','exp','geo','glossaire','testimonials')
   GROUP BY post_type;
   ```
4. Draft/update through one `wp eval-file` PHP script looping over bad IDs. Do not call `wp post update` once per row from `execute_code`; 50-tool-call cap can stop mid-run.
5. Generic fallback suffixes by post type worked well for deterministic repairs:
   - `glossaire`: definition + role in IP/innovation/business strategy.
   - `testimonials`: client proof + work type.
   - `exp`: service benefit + secure assets/projects.
   - `geo`: local presence + protect/finance/secure projects.
   - `post`: guide + understand enjeux/structure decisions.
   - `page`: page purpose + structure/secure innovation projects.
6. Verify with SQL count = 0 outside requested range.

Klarc final verification after fixing 111 published rows:

```text
bad 0
post_type      total  bad  min_len  max_len
events         4      0    145      159
exp            97     0    120      157
geo            2      0    147      147
glossaire      19     0    139      157
page           36     0    120      159
post           68     0    120      159
testimonials   26     0    120      156
```
