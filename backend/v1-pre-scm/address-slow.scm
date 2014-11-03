(declare (usual-integrations))

(define-structure (address (constructor %make-address))
  index)

(define-integrable (address<? a1 a2)
  (fix:< (address-index a1) (address-index a2)))

(define address-wt-tree-type (make-wt-tree-type address<?))
