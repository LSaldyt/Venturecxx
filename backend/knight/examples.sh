python -m venture.knight.driver -e '((x) -> { x })(2)' # (0, 2)
python -m venture.knight.driver -e 'normal(2, 1)' # (0, x) where x ~ normal(2, 1)
python -m venture.knight.driver -e 'get_current_trace()' # (0, An empty trace)
python -m venture.knight.driver -e 'trace_has(get_current_trace())' # (0, False)
python -m venture.knight.driver -e '{ t = get_current_trace(); _ = trace_set(t, 5); trace_get(t) }' # (0, 5)
