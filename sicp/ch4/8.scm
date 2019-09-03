(load "7.scm")

(define (make-define var value)
  (cons 'define (cons var value)))

(define (named-let? exp)
  (pair? (car exp)))

(define (let-bindings exp)
  (if (named-let? exp)
      (cadr exp)
      (car exp)))

(define (let-body exp)
  (if (named-let? exp)
      (cddr exp)
      (cdr exp)))

(define (let->combination exp)
  (define (parameters exp)
    (map car (let-bindings exp)))
  (define (initial-arguments exp)
    (map cadr (let-bindings exp)))
  (let ((proc-name (car exp)))
    (make-begin
      (list
        (make-define
          (cons proc-name (parameters exp))
          (let-body exp))
        (cons proc-name (initial-arguments exp))))))
