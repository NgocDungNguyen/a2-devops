const { chromium } = require('@playwright/test')

async function main() {
    const baseURL =
        process.env.E2E_BASE_URL ||
        process.env.BASE_URL ||
        'http://127.0.0.1'

    console.log('========================================')
    console.log('RMIT Store API Diagnostic')
    console.log('========================================')
    console.log(`[BASE URL] ${baseURL}`)

    const browser = await chromium.launch({
        headless: true
    })

    const page = await browser.newPage()

    /*
     * ---------------------------------------------------------
     * Browser console
     * ---------------------------------------------------------
     */
    page.on('console', message => {
        console.log(
            `[BROWSER ${message.type().toUpperCase()}] ${message.text()}`
        )
    })

    page.on('pageerror', error => {
        console.log('')
        console.log('========================================')
        console.log('BROWSER JAVASCRIPT ERROR')
        console.log('========================================')

        console.log(error.stack || error.message)
    })

    /*
     * ---------------------------------------------------------
     * Network requests
     * ---------------------------------------------------------
     */
    page.on('request', request => {
        const url = request.url()

        if (
            url.includes('/api/') ||
            url.includes(':8000')
        ) {
            console.log(
                `[APP REQUEST] ${request.method()} ${url}`
            )
        }
    })

    /*
     * ---------------------------------------------------------
     * Network responses
     *
     * IMPORTANT:
     * Print response BODY for API requests.
     * ---------------------------------------------------------
     */
    page.on('response', async response => {
        const url = response.url()

        if (
            !url.includes('/api/') &&
            !url.includes(':8000')
        ) {
            return
        }

        console.log(
            `[APP RESPONSE] ${response.status()} ${url}`
        )

        /*
         * Print bodies only for important APIs.
         */
        if (
            url.includes('/api/products/') ||
            url.includes('/api/categories/') ||
            url.includes('/api/brands/')
        ) {
            try {
                const body = await response.text()

                console.log('')
                console.log('----------------------------------------')
                console.log(`RESPONSE BODY: ${url}`)
                console.log('----------------------------------------')
                console.log(body)
                console.log('----------------------------------------')
                console.log('')

            } catch (error) {
                console.log(
                    `[BODY READ ERROR] ${error.message}`
                )
            }
        }
    })

    page.on('requestfailed', request => {
        console.log('')
        console.log('========================================')
        console.log('REQUEST FAILED')
        console.log('========================================')

        console.log(
            `${request.method()} ${request.url()}`
        )

        console.log(
            JSON.stringify(
                request.failure(),
                null,
                2
            )
        )
    })

    /*
     * ---------------------------------------------------------
     * Open shop page
     * ---------------------------------------------------------
     */
    console.log('')
    console.log('========================================')
    console.log('Opening /shop')
    console.log('========================================')

    await page.goto(
        `${baseURL}/shop`,
        {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        }
    )

    /*
     * ---------------------------------------------------------
     * Runtime config
     * ---------------------------------------------------------
     */
    const runtimeConfig = await page.evaluate(() => {
        return window.CONFIG || null
    })

    console.log('')
    console.log('========================================')
    console.log('window.CONFIG')
    console.log('========================================')

    console.log(
        JSON.stringify(runtimeConfig, null, 2)
    )

    /*
     * ---------------------------------------------------------
     * Fetch product API ourselves.
     *
     * This tells us EXACTLY what JSON structure the frontend
     * receives.
     * ---------------------------------------------------------
     */
    console.log('')
    console.log('========================================')
    console.log('DIRECT PRODUCT API FETCH')
    console.log('========================================')

    const productsResult = await page.evaluate(async () => {
        try {
            const response = await fetch(
                '/api/products/?ordering=newest&page=1&page_size=12'
            )

            const text = await response.text()

            let parsed = null

            try {
                parsed = JSON.parse(text)
            } catch (_) {
                // Leave parsed null if response is not JSON.
            }

            return {
                url: response.url,
                ok: response.ok,
                status: response.status,
                contentType: response.headers.get('content-type'),
                text,
                parsed
            }

        } catch (error) {
            return {
                ok: false,
                error: error.message
            }
        }
    })

    console.log(
        JSON.stringify(
            productsResult,
            null,
            2
        )
    )

    /*
     * ---------------------------------------------------------
     * Inspect response shape
     * ---------------------------------------------------------
     */
    console.log('')
    console.log('========================================')
    console.log('PRODUCT RESPONSE SHAPE')
    console.log('========================================')

    if (
        productsResult &&
        productsResult.parsed
    ) {
        const parsed = productsResult.parsed

        console.log(
            '[TOP LEVEL TYPE]',
            Array.isArray(parsed)
                ? 'array'
                : typeof parsed
        )

        if (
            parsed &&
            typeof parsed === 'object' &&
            !Array.isArray(parsed)
        ) {
            console.log(
                '[TOP LEVEL KEYS]',
                Object.keys(parsed)
            )

            console.log(
                '[HAS results]',
                Object.prototype.hasOwnProperty.call(
                    parsed,
                    'results'
                )
            )

            console.log(
                '[HAS data]',
                Object.prototype.hasOwnProperty.call(
                    parsed,
                    'data'
                )
            )

            console.log(
                '[HAS items]',
                Object.prototype.hasOwnProperty.call(
                    parsed,
                    'items'
                )
            )

            console.log(
                '[HAS count]',
                Object.prototype.hasOwnProperty.call(
                    parsed,
                    'count'
                )
            )

            if (Array.isArray(parsed.results)) {
                console.log(
                    `[results.length] ${parsed.results.length}`
                )
            }

            if (Array.isArray(parsed.data)) {
                console.log(
                    `[data.length] ${parsed.data.length}`
                )
            }

            if (Array.isArray(parsed.items)) {
                console.log(
                    `[items.length] ${parsed.items.length}`
                )
            }
        }

        if (Array.isArray(parsed)) {
            console.log(
                `[array.length] ${parsed.length}`
            )
        }
    }

    /*
     * Give Vue time to finish attempting its rendering.
     */
    console.log('')
    console.log('Waiting for Vue...')

    await page.waitForTimeout(5000)

    /*
     * ---------------------------------------------------------
     * DOM state
     * ---------------------------------------------------------
     */
    const productCount =
        await page.locator('.product-card').count()

    console.log('')
    console.log('========================================')
    console.log('FRONTEND RESULT')
    console.log('========================================')

    console.log(
        `[PRODUCT CARD COUNT] ${productCount}`
    )

    console.log(
        `[FINAL PAGE URL] ${page.url()}`
    )

    /*
     * Print page text as another useful clue.
     */
    const bodyText = await page
        .locator('body')
        .innerText()
        .catch(() => '')

    console.log('')
    console.log('========================================')
    console.log('PAGE TEXT')
    console.log('========================================')

    console.log(
        bodyText.slice(0, 3000)
    )

    await browser.close()

    console.log('')
    console.log('========================================')
    console.log('Diagnostic complete')
    console.log('========================================')
}

main()
    .then(() => {
        process.exit(0)
    })
    .catch(error => {
        console.error('')
        console.error('========================================')
        console.error('DIAGNOSTIC FAILED')
        console.error('========================================')

        console.error(error)

        process.exit(1)
    })
