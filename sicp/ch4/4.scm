(load "3.scm")

; direct way
(define (eval-and exp env)
  (define (expand-and exp)
    (let ((leftmost (eval (car exp) env)))
      (if (true? leftmost)
          (if (null? (cdr exp))
              leftmost
              (expand-and (cdr exp)))
          'false)))
  (if (null? exp)
      'true
      (expand-and exp)))

(put 'and 'eval eval-and)

(define (eval-or exp env)
  (define (expand-or exp)
    (if (null? exp)
        'false
        (let ((leftmost (eval (car exp) env)))
          (if (true? leftmost)
              leftmost
              (expand-or (cdr exp))))))
  (expand-or exp))

(put 'or 'eval eval-or)

; derived way
; the following code is NOT complete
; until lambda is handled correctly
(define (make-if predicate consequent alternative)
  (list 'if predicate consequent alternative))

(define (make-lambda parameters body)
  (cons 'lambda (cons parameters body)))

(define (and->if exps)
  (if (null? (cdr exps))
      (list
        (make-lambda '(exp)
                     (list (make-if 'exp 'exp 'false)))
        (car exps))
      (make-if (car exps)
               (and->if (cdr exps))
               'false)))

(put 'and 'eval (lambda (exp env)
                  (eval (and->if exp) env)))

(define (or->if exps)
  (if (null? exps)
      'false
      (list
        (make-lambda '(exp)
                     (list (make-if 'exp 'exp (or->if (cdr exps)))))
        (car exps))))

(put 'or 'eval (lambda (exp env)
                 (eval (of->if exp) env)))
