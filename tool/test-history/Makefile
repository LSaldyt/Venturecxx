
# The data file is generated by
# /var/lib/jenkins/jobs/venture-inference-quality/builds
# for b in `seq 1 185`; do echo -n "$b "; grep FAILED $b/log | head -1 | cut -f 3-4 -d '=' | cut -f 1 -d ')'; done; 
# for b in `seq 1 185`; do echo -n "$b "; grep SUCCESS $b/log; done; 
# and manual munging (e.g., adding error and failure counts)

failures.png:
	cat data.conf | gnuplot

# The second data file is generated by
# for b in `seq 1 185`; do echo -n "$b "; grep Ran $b/log | head -1 | cut -f 2 -d ' '; done; 
# and manual munging
counts.png:
	cat test-counts.conf | gnuplot
