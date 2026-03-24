describe('server i18n language detection', () => {
  it('detects Polish when the browser prefers Polish', async () => {
    const { createServerI18n } = await import('../i18n.server');

    const instance = await createServerI18n('pl-PL,pl;q=0.9,en;q=0.8');

    expect(instance.language).toBe('pl');
    expect(instance.resolvedLanguage).toBe('pl');
  });
});
