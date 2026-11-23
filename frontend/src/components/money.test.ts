import { expect, it } from 'vitest'
import { money } from './TransactionTable'
it('conserva centavos de totales superiores al entero seguro de JavaScript', () => {
  expect(money('9899999999999901')).toBe('$98,999,999,999,999.01')
  expect(money(1234)).toBe('$12.34')
})
