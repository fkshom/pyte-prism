PytePrism - A Page Object Model DSL for Python
==========================================================
inspired by Ruby SitePrism https://github.com/site-prism/site_prism


Synopsis
-----------
Here's an overview of how PytePrism is designed to be used:

.. code-block:: Python

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from pyte_prism import Page, PageSection, Element, Section, Sections
    
    class Menu(PageSection):
      gmail = Element(By.XPATH, "//a[text()='Gmail']")
      images = Element(By.XPATH, "//a[text()='Images']")
    
    class SearchResult(PageSection):
      title = Element(By.CSS_SELECTOR, "div.r > a > h3")
      title_link = Element(By.CSS_SELECTOR, "div.r > a")
      blurb = Element(By.CSS_SELECTOR, "div.s > div > span")
    
    class Home(Page):
      _url = "https://www.google.com/"
    
      search_field = Element(By.CSS_SELECTOR, "input[name='q'")
      search_button = Element(By.CSS_SELECTOR, "div.FPdoLc.tfB0Bf input[name='btnK']")
      footer_links = Element(By.CSS_SELECTOR, "#footer a")
      menu = Section(Menu, By.CSS_SELECTOR, "#gbw")
    
    class SearchResults(Page):
      _url_matcher = "https://www.google.com/results\?.*"
    
      menu = Section(Menu, By.CSS_SELECTOR, "#gbw")
      search_results = Sections(SearchResult, By.CSS_SELECTOR, "#search > div > div > div.g")
    
      def search_result_links(self):
        return [result.title.get_attribute('href') for result in self.search_results]
    
    def main():
      driver = webdriver.Chrome()
    
      home = Home(driver)
      home.load()
      home.wait_until_menu_visible()  # menu loads after a second or 2, give it time to arrive
    
      print(home.has_menu())          #=> True
      print(home.has_search_field())  #=> True
      print(home.has_search_button()) #=> True
    
      home.search_field.send_keys("Sausages")
      home.search_field.send_keys(Keys.ESCAPE) # Close suggestion box
      home.wait_until_search_button_visible()  # Wait until suggestion box close
      home.search_button.click()
    
      results_page = SearchResults(driver)
      results_page.is_loaded()  #=> True ( Does _url_matcher matches current_url? )
      results_page.wait_until_search_results_visible(timeout=30)  # default timeout is 10 sec
      print(len(results_page.search_results))  #=> about 10
    
      titles = [result.title.text for result in results_page.search_results]
      links =  [result.title_link.get_attribute('href') for result in results_page.search_results]
      descr =  [result.blurb.text for result in results_page.search_results]
    
      from pprint import pprint
      pprint(list(zip(titles, links, descr)))
      """
      #=> [('Sausage - Wikipedia', 'https://en.wikipedia.org/wiki/Sausage', 'Sausages are ...'),
      #    ('List of sausages - Wikipedia', 'https://en.wikipedia.org/wiki/List_of_sausages', 'This is a lias of ...'),
      #    ...]
      """
    
    if __name__ == "__main__":
        main()
    
Requirements
----------------

- Python 3

Features
-----------

- Multiple platforms support: Linux, macOS, Windows
- Pure python

The Installation
------------------

From Pypi with the Python package manager:

.. code-block:: console
    
    pip install pyte-prism
    
To install the cutting edge version from the git repository:

.. code-block:: console
    
    git clone https://github.com/fkshom/pyte-prism.git
    cd pyte-prism
    python setup.py install

Examples
-----------

.. code-block:: python

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from pyte_prism import Page, PageSection, PageIframe, Element, Section, Sections, Iframe

    # Section must inherit PageSection class
    class MySection(PageSection):
      title = Element(By.XPATH, "//div[@class='title']")

    # Iframe must inherit PageIframe class    
    class MyIframe(PageIframe):
      title = Element(By.XPATH, "//div[@class='title']")

    # Page must inherit Page class
    class Home(Page):
      _url = "http://example.com/"                # _url is used by Page.load() method.
      _url_matcher = r"https?://example.com/.*"   # _url_matcher is used by Page.is_loaded() method.

      # definition of element
      go_button = Element(By.ID, "#button")
      keyword_box = Element(By.ID, "#keyword")
      items = Elements(By.CSS_SELECTOR, "ul#items > li")
      section = Setion(MySection, By.ID, "#section")
      sections = Sections(MySection, By.ID, "#sections")   # MySection is not typo
      myiframe = IFrame(MyIframe, BY.ID, "#iframe")
    
    def main():
      driver = webdriver.Chrome()
      home = Home(driver)
      home.load()                    # visit to "_url"
      home.wait_until_page_loaded()  # check current_url is  _url or _url_matcher (if defined)
      home.assert_loaded()           # raise Exception if is_loaded() is False.
      home.wait_until_page_readystate_is_complete(timeout=10)  # wait until javascript readyState is complete.

      
      # Defined some supported methods automatically
      # home.wait_until_<variablename>_visible()          # None or Exception
      # home.wait_until_<variablename>_invisible()        # None or Exception
      # home.wait_until_<variablename>_to_be_clickable()  # None or Exception
      # home.has_<variablename>()                         # True or False
      # home.has_no_<variablename>()                      # True or False
      
      home.keyword_box.send_keys('my keyword')            # element is webdriver element.

      home.wait_until_go_button_visible(timeout=30)       # timeout: default 10
      home.go_button.click()

      home.section.title.text
      home.sections[0].title.text

      # swtich to, exit from iframe context automatically
      with home.myiframe as iframe:
        iframe.title.text

Parametrized URLs
^^^^^^^^^^^^^^^^^

PytePrism uses the uritemplate module and therefore allows for parameterization of URLs.
see https://uritemplate.readthedocs.io/en/latest/

.. code-block:: python

    class Home(Page):
      _url = 'http://example.com/users{/userid}'    
      _url_matcher = 'https?://example.com/users.*'

    class Home2(Page):
      _url = 'http://example.com/search{?keyword,lang}'
      _url_matcher = 'https?://example.com/search.*'

    def main():
      driver = webdriver.Chrome()
      home = Home(driver)
      home.load()             # visit to http://example.com/users
      home.load(userid=100)   # visit to http://example.com/users/100

      home2 = Home2(driver)
      home2.load(keyword='mykeyword', lang='en')   # visit to http://example.com/saearch?keyword=mykeyword&lang=en

