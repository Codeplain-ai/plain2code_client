describe('Hello World App', () => {
  it('displays "hello, world"', () => {
    cy.visit('/');
    cy.contains('div', 'hello, world').should('be.visible');
  });
});