articles = [
    ("elevenlabs-review.html", "elevenlabs-review"),
    ("runpod-review.html", "runpod-review"),
    ("surfer-seo-review.html", "surfer-seo-review"),
    ("mixo-vs-carrd-vs-wix.html", "mixo_carrd_comparison"),
    ("elevenlabs-vs-speechify.html", "elevenlabs_speechify_comparison"),
    ("runpod-vs-vast-vs-lambda.html", "runpod_vast_lambda_comparison"),
]

email_capture_html = '''

        <!-- Email Capture in Article -->
        <section class="email-capture-article" style="background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 30px; margin: 40px 0; text-align: center;">
            <h3 style="margin: 0 0 10px; color: #1a1a1a;">📧 Guide gratis: Zero-Capital Affiliate Marketing</h3>
            <p style="margin: 0 0 20px; color: #555;">7-Tage-Checkliste, Templates, Tool-Stack für 0€ – direkt ins Postfach.</p>
            <form id="email-form-article" style="display: flex; gap: 10px; max-width: 400px; margin: 0 auto; flex-wrap: wrap; justify-content: center;">
                <input type="email" name="email" placeholder="deine@email.de" required autocomplete="email" style="flex: 1; min-width: 200px; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 1rem;">
                <button type="submit" class="cta-button" style="padding: 12px 24px;">Gratis holen</button>
            </form>
            <p id="email-message-article" style="margin: 12px 0 0; font-size: 0.85rem; min-height: 20px;"></p>
            <p style="margin: 12px 0 0; font-size: 0.75rem; color: #888;">Kein Spam. Jederzeit abmeldbar. <a href="/lead-magnet/" style="color: #007bff;">Guide auch ohne Anmeldung lesen</a></p>
        </section>'''

email_capture_js_template = '''
        // Email capture form handler (article)
        (function() {
            const form = document.getElementById('email-form-article');
            const messageEl = document.getElementById('email-message-article');
            if (!form) return;

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = form.querySelector('input[name="email"]').value.trim();
                const submitBtn = form.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.textContent;
                
                if (!email || !email.includes('@')) {
                    messageEl.innerHTML = '<span style="color: #dc3545;">❌ Bitte gültige E-Mail eingeben</span>';
                    return;
                }

                submitBtn.disabled = true;
                submitBtn.textContent = 'Wird gesendet...';
                messageEl.textContent = '';

                try {
                    const res = await fetch('/api/email/subscribe', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            email,
                            source: 'article_PLACEHOLDER_SLUG',
                            utm_source: 'organic',
                            utm_medium: 'email_capture',
                            utm_campaign: 'lead_magnet',
                            utm_content: 'article_footer'
                        })
                    });
                    const data = await res.json();
                    
                    if (data.status === 'subscribed' || data.status === 'confirmation_resent') {
                        messageEl.innerHTML = '<span style="color: #28a745;">✅ ' + data.message + '</span>';
                        form.reset();
                        track('email_subscribe', {source: 'article_footer', article: 'PLACEHOLDER_SLUG', email: email});
                    } else if (data.status === 'already_subscribed') {
                        messageEl.innerHTML = '<span style="color: #ffc107;">ℹ️ ' + data.message + '</span>';
                    } else {
                        messageEl.innerHTML = '<span style="color: #dc3545;">❌ ' + (data.error || data.message || 'Fehler') + '</span>';
                    }
                } catch (err) {
                    messageEl.innerHTML = '<span style="color: #dc3545;">❌ Netzwerkfehler. Bitte erneut versuchen.</span>';
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            });
        })();'''

for filename, slug in articles:
    filepath = f"/root/7day-income-site/{filename}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add email capture form before </article>
    content = content.replace('</article>', email_capture_html + '\n    </article>')
    
    # Add JS handler before </script> with slug replacement
    js_with_slug = email_capture_js_template.replace('PLACEHOLDER_SLUG', slug)
    content = content.replace('window.track = track;\n        })();\n    </script>', 
                              'window.track = track;\n        })();' + js_with_slug + '\n    </script>')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {filename}")

print("All articles updated!")