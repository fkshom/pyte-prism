import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from uritemplate import expand as uriexpand
from logging import getLogger

__version__ = '0.0.4'
logger = getLogger(__name__)

def logged(func):
  def wrapper(*args, **kwargs):
    try:
      qualfuncname = f"{func.__qualname__}"
      logger.info(f"started {qualfuncname}, params: {args} and {kwargs}")
      return func(*args, **kwargs)
    except Exception as e:
      logger.exception(e)
  return wrapper

class Element(object):
  def __init__(self, by, selector):
    self.by = by
    self.selector = selector

  def __get__(self, obj, klass):
    if hasattr(obj, 'base_element') and obj.base_element is not None:
      return obj.base_element.find_element(self.by, self.selector)
    else:
      return obj.driver.find_element(self.by, self.selector)

class Elements(object):
  def __init__(self, by, selector):
    self.by = by
    self.selector = selector

  def __get__(self, obj, klass):
    if hasattr(obj, 'base_element') and obj.base_element is not None:
      return obj.base_element.find_elements(self.by, self.selector)
    else:
      return obj.driver.find_elements(self.by, self.selector)

class SupportMethodGenerator(object):
  def __init__(self, timeout=10):
    self.timeout = timeout

  def wait_until_element_visible(self, by, selector):
    this = self
    def inner(self, timeout=this.timeout):
      wait = WebDriverWait(self.driver, timeout)
      wait.until(
        EC.visibility_of_element_located((by, selector))
      )
      return self.driver.find_element(by, selector)
    return inner

  def wait_until_element_invisible(self, by, selector):
    this = self
    def inner(self, timeout=this.timeout):
      wait = WebDriverWait(self.driver, timeout)
      wait.until(
        EC.invisibility_of_element_located((by, selector))
      )
      return None
    return inner

  def wait_until_element_to_be_clickable(self, by, selector):
    this = self
    def inner(self, timeout=this.timeout):
      wait = WebDriverWait(self.driver, timeout)
      wait.until(
        EC.element_to_be_clickable((by, selector))
      )
      return self.driver.find_element(by, selector)
    return inner

  def has_element(self, by, selector):
    this = self
    def inner(self):
      try:
        self.driver.find_element(by, selector)
        return True
      except NoSuchElementException:
        return False
    return inner

  def has_no_element(self, by, selector):
    this = self
    def inner(self):
      try:
        self.driver.find_element(by, selector)
        return False
      except NoSuchElementException:
        return True
    return inner

  def element_element(self, by, selector):
    this = self
    def inner(self):
      return self.driver.find_element(by, selector)
    return inner

  def element_elements(self, by, selector):
    this = self
    def inner(self):
      return self.driver.find_elements(by, selector)
    return inner

class Section(object):
  def __init__(self, klass, base_by, base_selector):
    self.klass = klass
    self.base_by = base_by
    self.base_selector = base_selector

  def __get__(self, obj, klass):
    base_element = obj.driver.find_element(self.base_by, self.base_selector)
    return self.klass(obj.driver, base_element=base_element)

class Sections(object):
  def __init__(self, klass, base_by, base_selector):
    self.klass = klass
    self.base_by = base_by
    self.base_selector = base_selector

  def __get__(self, obj, klass):
    base_elements = obj.driver.find_elements(self.base_by, self.base_selector)
    return [self.klass(obj.driver, base_element=base_element) for base_element in base_elements]

class Iframe(object):
  def __init__(self, klass, base_by, base_selector):
    self.klass = klass
    self.base_by = base_by
    self.base_selector = base_selector

  def __get__(self, obj, klass):
    iframe_element = obj.driver.find_element(self.base_by, self.base_selector)
    return self.klass(obj.driver, iframe_element=iframe_element)

class PageMetaclass(type):
  def __new__(cls, name, bases, dict_):
    for k, v in list(dict_.items()):
      if isinstance(v, Element) or isinstance(v, Elements):
        smg = SupportMethodGenerator()
        dict_[f"wait_until_{k}_visible"] = smg.wait_until_element_visible(v.by, v.selector)
        dict_[f"wait_until_{k}_invisible"] = smg.wait_until_element_invisible(v.by, v.selector)
        dict_[f"wait_until_{k}_to_be_clickable"] = smg.wait_until_element_to_be_clickable(v.by, v.selector)
        # Elementsのときもfind_elementが使われるため、「少なくとも1つのelementがあるかどうか」が検査される
        dict_[f"has_{k}"] = smg.has_element(v.by, v.selector)
        dict_[f"has_no_{k}"] = smg.has_no_element(v.by, v.selector)

        if isinstance(v, Element):
          dict_[f"{k}_element"] = smg.element_element(v.by, v.selector)
        elif isinstance(v, Elements):
          dict_[f"{k}_elements"] = smg.element_elements(v.by, v.selector)

      if isinstance(v, Section) or isinstance(v, Sections) or isinstance(v, Iframe):
        smg = SupportMethodGenerator()
        dict_[f"wait_until_{k}_visible"] = smg.wait_until_element_visible(v.base_by, v.base_selector)
        dict_[f"wait_until_{k}_invisible"] = smg.wait_until_element_invisible(v.base_by, v.base_selector)
        # Sectionsのときもfind_elementが使われるため、「少なくとも1つのelementがあるかどうか」が検査される
        dict_[f"has_{k}"] = smg.has_element(v.base_by, v.base_selector)
        dict_[f"has_no_{k}"] = smg.has_no_element(v.base_by, v.base_selector)

        if isinstance(v, Section):
          dict_[f"{k}_element"] = smg.element_element(v.base_by, v.base_selector)
        elif isinstance(v, Sections):
          dict_[f"{k}_elements"] = smg.element_elements(v.base_by, v.base_selector)
        elif isinstance(v, Iframe):
          dict_[f"{k}_element"] = smg.element_element(v.base_by, v.base_selector)


    return type.__new__(cls, name, bases, dict_)

class Page(object, metaclass=PageMetaclass):
  _url = None
  _url_matcher = None

  def __init__(self, driver):
    self.driver = driver

  @logged
  def load(self, **kwargs):
    if self._url:
      uri = uriexpand(self._url, **kwargs)
      self.driver.get(uri)
    else:
      raise Exception(f"Cant load. {self.__class__} has not _url parameter")

  @logged
  def is_loaded(self):
    if self._url_matcher:
      if re.fullmatch(self._url_matcher, self.current_url):
        return True
      else:
        return False
    elif self._url:
      if self._url == self.current_url:
        return True
      else:
        return False
    else:
      raise Exception(f"Cant load check. {self.__class__} has neither _url and _url_matcher parameter")

    if self._url_matcher is not None and re.fullmatch(self._url_matcher, self.current_url):
      return True
    else:
      return False

  @logged
  def assert_loaded(self):
    if self.is_loaded():
       return True
    else:
      raise Exception(f"Page {self.__class__} is not loaded.")

  @logged
  def wait_until_page_loaded(self, timeout=10):
    for i in range(1, timeout+1):
      logger.debug(f"checking page is loaded {i}/{timeout}")
      if self.is_loaded():
        logger.debug(f"page is loaded!")
        break
      time.sleep(1)
    else:
      raise Exception(f"Timeout loading Page {self.__class__}")

  @logged
  def wait_until_page_readystate_is_complete(self, timeout=10):
    for i in range(1, timeout+1):
      logger.debug(f"checking document.readyState {i}/{timeout}")
      if self.driver.execute_script("return document.readyState") == "complete":
        logger.debug(f"document.readyState is complete!")
        break
      time.sleep(1)
    else:
      raise Exception(f"Timeout loading Page {self.__class__}")

  @property
  def current_url(self):
    return self.driver.current_url

class PageSection(object, metaclass=PageMetaclass):
  def __init__(self, driver, base_element):
    self.driver = driver
    self.base_element = base_element

  def __enter__(self):
    return self

  def __exit__(self, *args):
    pass

class PageIframe(object, metaclass=PageMetaclass):
  def __init__(self, driver, iframe_element):
    self.driver = driver
    self.iframe_element = iframe_element

  def __enter__(self):
    self.driver.switch_to_frame(self.iframe_element)
    return self

  def __exit__(self, *args):
    self.driver.switch_to.default_content()
