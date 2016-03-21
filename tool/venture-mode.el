;;; Copyright (c) 2015 MIT Probabilistic Computing Project.
;;;
;;; This file is part of Venture.
;;;
;;; Venture is free software: you can redistribute it and/or modify
;;; it under the terms of the GNU General Public License as published by
;;; the Free Software Foundation, either version 3 of the License, or
;;; (at your option) any later version.
;;;
;;; Venture is distributed in the hope that it will be useful,
;;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;;; GNU General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with Venture.  If not, see <http://www.gnu.org/licenses/>.

;; Syntax highlighting and indentation for Venture
;; To active, include the following in emacs .init file
;; (load [path-to-this-file])
;; (require 'venture-mode)


(require 'scheme)

;;;###autoload
(define-derived-mode venture-mode scheme-mode "Venture"
  "Major mode for editing Venture code.
Editing commands are similar to those of `lisp-mode'.

Commands:
Delete converts tabs to spaces as it moves back.
Blank lines separate paragraphs.  Semicolons start comments.
\\{scheme-mode-map}
Entering this mode runs the hooks `scheme-mode-hook' and then
`venture-mode-hook'."
  (setq font-lock-defaults '((venture-font-lock-keywords
                              venture-font-lock-keywords-1
                              venture-font-lock-keywords-2
                              venture-font-lock-keywords-3)
                             nil t (("_" . "w"))
                             beginning-of-defun
                             (font-lock-mark-block-function . mark-defun)))
  (setq-local imenu-generic-expression venture-imenu-generic-expression)
  (setq-local imenu-syntax-alist '(("_" . "w")))
  (setq-local lisp-indent-function 'venture-indent-function)
  (set (make-local-variable 'imenu-syntax-alist)
       '(("_" . "w"))))

;; Not actually sure what this does, but the scheme-mode file has it; apparently it's good
(defcustom venture-mode-hook nil
  "Normal hook run when entering `venture-mode'.
See `run-hooks'."
  :type 'hook
  :group 'venture)

(defvar venture-imenu-generic-expression
  '((nil
     "^\\[\\(assume\\|define\\)\\s-+\\(\\sw+\\)" 2)
    ("Nested assumes"
     "(assume\\s-+\\(\\sw+\\)" 1))
  "Imenu generic expression for Venture mode.  See `imenu-generic-expression'.")

(defvar font-lock-language-shift-face 'font-lock-language-shift-face
  "Face name used for symbols causing the program to enter the modeling language")

(defface font-lock-language-shift-face
  '((((class grayscale) (background light)) :foreground "LightGray" :weight bold)
    (((class grayscale) (background dark))  :foreground "DimGray" :weight bold)
    (((class color) (min-colors 88) (background light)) :foreground "firebrick")
    (((class color) (min-colors 88) (background dark))  :foreground "firebrick")
    (((class color) (min-colors 16) (background light)) :foreground "firebrick")
    (((class color) (min-colors 16) (background dark)) :foreground "firebrick")
    (((class color) (min-colors 8)) :foreground "red" :weight bold)
    (t :weight bold))
  "Font Lock mode face used for symbols causing the program to enter the modeling language."
  :group 'font-lock-faces)

(defvar venture-font-lock-keywords-1 nil)
(setq venture-font-lock-keywords-1
      ;; Declarations, by analogy with scheme-mode
      (eval-when-compile
        (list
         (list "[([]\\(define\\)\\>[ \t]*\\(\\sw+\\)\\>"
               '(1 font-lock-keyword-face)
               '(2 font-lock-function-name-face))
         (list "[([]\\(assume\\)\\>[ \t]*\\(\\sw+\\)\\>"
               '(1 font-lock-language-shift-face)
               '(2 font-lock-function-name-face)))))

(defvar venture-font-lock-keywords-2 nil)
(setq venture-font-lock-keywords-2
      ;; Control structures, special forms, modeling commands
      (append venture-font-lock-keywords-1
              (eval-when-compile
                (list
                 (list (concat "(" (regexp-opt '(;; Model special forms
                                                 "cond" "if" "lambda" "let" "letrec"
                                                 "and" "or" "identity") t)
                               "\\>")
                       '(1 font-lock-keyword-face))
                 (list (concat "(" (regexp-opt '(;; Inference special forms
                                                 "loop" "do" "begin"
                                                 "call_back" "load") t)
                               "\\>")
                       '(1 font-lock-keyword-face))
                 (list (concat "\\<" (regexp-opt
                                      '(;; Inference scopes
                                        "default" "all" "one" "none"
                                        "ordered") t) "\\>")
                       '(1 font-lock-builtin-face))
                 (list (concat "[([]" (regexp-opt
                                       '(;; Inference special forms that introduce model context
                                         ;; Also infer, even though its body is in the inference language
                                         "assume" "observe" "predict" "infer"
                                         "predict_all"
                                         "sample" "sample_all" "collect" "force"
                                         ) t) "\\>")
                       '(1 font-lock-language-shift-face))
                 ))))

(defvar venture-font-lock-keywords-3 nil)
(setq venture-font-lock-keywords-3
      ;; These are likely to change over time. To get an updated list, run
      ;;   tool/venture_mode_font_lock.py builtins
      ;; [The script also supports a few subsets Call with no
      ;; arguments for list of valid arguments to pass.]
      ;; Unfortunately, the resulting list will not be perfect. For instance,
      ;; "forget" and "freeze" show up as inference SP's, but are also included
      ;; up above as directives. Fortunately, font-lock-keywords with lower
      ;; numbers take precedence.
      (append
       venture-font-lock-keywords-2
       (eval-when-compile
         (list
          (list
           (concat "\\<"
            (regexp-opt
             '(;; model SP's
               "add" "apply" "apply_function" "arange" "array" "assess" "atan2"
               "atom_eq" "bernoulli" "beta" "binomial" "biplex" "categorical"
               "contains" "cos" "debug" "diag_matrix" "dict" "dirichlet" "div" "eq"
               "eval" "exactly" "exp" "expon" "extend_environment" "fill" "first"
               "fix" "flip" "floor" "gamma" "get_current_environment"
               "get_empty_environment" "gt" "gte" "hypot" "id_matrix" "imapv" "int_div"
               "int_mod" "inv_gamma" "inv_wishart" "is_array" "is_atom" "is_boolean"
               "is_dict" "is_environment" "is_integer" "is_matrix" "is_number" "is_pair"
               "is_probability" "is_procedure" "is_simplex" "is_symbol" "is_vector" "laplace"
               "linspace" "list" "log" "log_bernoulli" "log_flip" "lookup" "lt" "lte"
               "make_beta_bernoulli" "make_cmvn" "make_crp" "make_csp" "make_dir_cat"
               "make_gp" "make_lazy_hmm" "make_suff_stat_bernoulli" "make_sym_dir_cat"
               "make_uc_beta_bernoulli" "make_uc_dir_cat" "make_uc_sym_dir_cat" "mapv"
               "matrix" "matrix_add" "matrix_mul" "matrix_times_vector" "mem" "min" "mul"
               "multivariate_normal" "normal" "not" "pair" "poisson" "pow" "probability"
               "ravel" "real" "rest" "scale_matrix" "scale_vector" "second" "simplex" "sin"
               "size" "sqrt" "student_t" "sub" "symmetric_dirichlet" "tag" "tag_exclude"
               "take" "tan" "to_array" "to_list" "to_vector" "transpose" "uniform_continuous"
               "uniform_discrete" "value_error" "vector" "vector_add" "vector_dot"
               "vector_times_matrix" "vonmises" "wishart" "xor" "zip"
               ;; inference SP's
               "assert" "bogo_possibilize" "collapse_equal" "collapse_equal_map" "detach"
               "detach_for_proposal" "draw_scaffold" "draw_subproblem" "emap" "empty"
               "enumerative_diversify" "forget" "freeze" "func_mh" "func_pgibbs" "func_pmap"
               "get_current_values" "gibbs" "gibbs_update" "hmc" "in_model" "incorporate"
               "into" "log_likelihood_at" "likelihood_weight" "load_plugin" "map" "meanfield"
               "mh" "mh_kernel_update" "model_import_foreign" "nesterov" "new_model"
               "ordered_range" "particle_log_weights" "pgibbs" "pgibbs_update" "plot"
               "plot_to_file" "plotf" "plotf_to_file" "log_joint_at" "print"
               "print_scaffold_stats" "printf" "pyeval" "pyexec" "regen" "regen_with_proposal"
               "rejection" "resample" "resample_multiprocess" "resample_serializing"
               "resample_thread_ser" "resample_threaded" "restore" "select"
               "set_particle_log_weights" "slice" "slice_doubling" "subsampled_mh"
               "subsampled_mh_check_applicability" "subsampled_mh_make_consistent" "sweep" 
               ;; inference prelude
               "accumulate_dataset" "action" "bind" "bind_" "curry" "curry3"
               "default_markov_chain" "for_each" "for_each_indexed" "global_log_likelihood"
               "global_log_joint" "imapM" "iterate" "join_datasets" "mapM" "pass" "conditional"
               "repeat" "reset_to_prior" "return" "run" "sequence" "sequence_"
               ;; inference callbacks
               "timer_pause" "timer_resume" "timer_start" "timer_time") t)
            "\\>")
           '(1 font-lock-builtin-face))))))

(defvar venture-font-lock-keywords nil
  "Default expressions to highlight in Venture")
(setq venture-font-lock-keywords venture-font-lock-keywords-1)

;; Candidate special forms to highlight:
;; report?

;; This is a hack; nearly a direct copy-paste of scheme-indent-function
;; Needed because "do" is indented differently in Scheme than in Venture;
;; if we didn't have a separate venture-indent-function, then the behavior
;; of "do" would get clobbered for Scheme mode
(defun venture-indent-function (indent-point state)
  "Scheme mode function for the value of the variable `lisp-indent-function'.
This behaves like the function `lisp-indent-function', except that:

i) it checks for a non-nil value of the property `venture-indent-function',
rather than `lisp-indent-function'.

ii) if that property specifies a function, it is called with three
arguments (not two), the third argument being the default (i.e., current)
indentation."
  (let ((normal-indent (current-column)))
    (goto-char (1+ (elt state 1)))
    (parse-partial-sexp (point) calculate-lisp-indent-last-sexp 0 t)
    (if (and (elt state 2)
             (not (looking-at "\\sw\\|\\s_")))
        ;; car of form doesn't seem to be a symbol
        (progn
          (if (not (> (save-excursion (forward-line 1) (point))
                      calculate-lisp-indent-last-sexp))
              (progn (goto-char calculate-lisp-indent-last-sexp)
                     (beginning-of-line)
                     (parse-partial-sexp (point)
                                         calculate-lisp-indent-last-sexp 0 t)))
          ;; Indent under the list or under the first sexp on the same
          ;; line as calculate-lisp-indent-last-sexp.  Note that first
          ;; thing on that line has to be complete sexp since we are
          ;; inside the innermost containing sexp.
          (backward-prefix-chars)
          (current-column))
      (let ((function (buffer-substring (point)
                                        (progn (forward-sexp 1) (point))))
            method)
        (setq method (get (intern-soft function) 'venture-indent-function))
        (cond ((or (eq method 'defun)
                   (and (null method)
                        (> (length function) 3)
                        (string-match "\\`def" function)))
               (lisp-indent-defform state indent-point))
              ((integerp method)
               (lisp-indent-specform method state
                                     indent-point normal-indent))
              (method
               (funcall method state indent-point normal-indent)))))))

;; Fix indentation for special forms that differ from venture
(put 'begin 'venture-indent-function 0)
(put 'do 'venture-indent-function 0)
(put 'lambda 'venture-indent-function 1)
(put 'let 'venture-indent-function 'scheme-let-indent)
(put 'letrec 'venture-indent-function 'scheme-let-indent)
(put 'define 'venture-indent-function 1)
(put 'assume 'venture-indent-function 1)
(put 'mem 'venture-indent-function 0)
(put 'scope_include 'venture-indent-function 0)
(put 'repeat 'venture-indent-function 1)

;; Provide
(provide 'venture-mode)

;; Make Emacs open .vnt files in venture-mode
;;;###autoload
(add-to-list 'auto-mode-alist '("\\.vnt\\'" . venture-mode))
