(load "../../ch3/25.scm")
(load "test.scm")

(load "basic.scm")
(load "quote.scm")
(load "begin.scm")
(load "sequence.scm")
(load "and.scm")
(load "or.scm")
(load "if.scm")
(load "lambda.scm")
(load "cond.scm")
(load "define.scm")
(load "assignment.scm")
(load "let.scm")

(load "repl.scm")

; data-directed programming table
(define eval-table
  (let ((table (make-table 'eval-table)))
    (lambda (op . args)
      (cond ((eq? op 'put)
             ((table 'insert!) (list (car args)) (cadr args)))
            ((eq? op 'get)
             ((table 'lookup) (list (car args))))
            (else (error "Unknown evel table operation -- " op))))))

(define interpreter (make-interpreter eval-table))

(install-syntax-quote eval-table)
(install-syntax-begin eval-table)
(install-syntax-sequence eval-table)
(install-syntax-and eval-table)
(install-syntax-or eval-table)
(install-syntax-if eval-table)
(install-syntax-lambda eval-table)
(install-syntax-cond eval-table)
(install-syntax-define eval-table)
(install-syntax-assignment eval-table)
(install-syntax-let eval-table)

; TODO: handle boolean more elegantly
(define (true? val) (not (false? val)))
(define (false? val) (eq? val false))

(define the-global-environment (eval-table 'get 'the-global-environment))
(define my-eval (interpreter 'eval))

; repl
(define output-prompt ";;; M-Eval value:")
(define (announce-output string)
  (newline)
  (display string)
  (newline))
(define (user-print object)
  (define procedure-parameters (eval-table 'get 'procedure-parameters))
  (define procedure-body (eval-table 'get 'procedure-body))
  (if (compound-procedure? object)
      (display (list 'compound-procedure
                     (procedure-parameters object)
                     (procedure-body object)
                     '<procedure-env>))
      (display object)))
(define repl (get-repl (lambda (input)
                         (my-eval input the-global-environment))
                       (lambda (result)
                         (announce-output output-prompt)
                         (user-print result))))
