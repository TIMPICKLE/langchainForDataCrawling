import asyncio
from langchain_openai import ChatOpenAI
from langchain.chains import create_extraction_chain
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import json


async def run_playwright(site):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # if True, may get the error: This browser is no longer supported. Please switch to a supported browser to continue using twitter.com. You can see a list of supported browsers in our He....
        # browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        # Set a timeout for navigating to the page
        try:
            # await page.goto(site, wait_until='load', timeout=20000) # 10 secs
            # await page.goto(site, wait_until='load')
            await page.goto(site, wait_until='networkidle')
        except TimeoutError:
            print("Timeout reached during page load, proceeding with available content.")
        page_source = await page.content()
        soup = BeautifulSoup(page_source, "html.parser")
        for script in soup(["script", "style"]): # Remove all javascript and stylesheet code
            script.extract()
        text = soup.get_text()
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines()) 
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  ")) 
        data = '\n'.join(chunk for chunk in chunks if chunk) # Drop blank lines
        await browser.close()
    return data

#并将代理设置为https://api.chatanywhere.tech 
GPT_4 = 'gpt-4'
llm = ChatOpenAI(
    temperature=0, 
    model=GPT_4, 
    openai_api_key='key',
    base_url='https://api.chatanywhere.tech/v1'  # 注意这里需要加上 /v1
)

async def main():
    website_info = {
        "url": "https://space.bilibili.com/282739748/video",
        "schema": {
            "name": "extract_videos_info",
            "description": "Extract all videos information from bilibili page",
            "parameters": {
                "type": "object",
                "properties": {
                    "videos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "The title of the video"},
                                "view_count": {"type": "string", "description": "Number of video views"},
                                "upload_date": {"type": "string", "description": "Video upload date"},
                                "duration": {"type": "string", "description": "Video duration"}
                            }
                        }
                    }
                },
                "required": ["videos"]
            }
        }
    }
    # website_info = {
    #     'url': 'https://books.toscrape.com/catalogue/masks-and-shadows_909/index.html',
    #     "schema": {
    #         "properties": {
    #             "title": {"type": "string"},
    #             "upc": {"type": "string"},
    #             "avaibility": {"type": "string"},
    #         },
    #     }
    # }

    output = await run_playwright(website_info['url'])
    
    # 使用新的 with_structured_output 方法
    structured_llm = llm.with_structured_output(website_info['schema'])
    json_result = structured_llm.invoke(output)
    
    # 保存到文件时格式化
    with open('fuck.txt', 'w', encoding='utf-8') as f:
        f.write(json.dumps(json_result, indent=4, ensure_ascii=False))
    print(json_result)


if __name__ == "__main__":
    asyncio.run(main())
