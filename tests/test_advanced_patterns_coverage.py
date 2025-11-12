"""
Tests for advanced Python patterns and API interactions
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict, Counter
from functools import reduce
import operator

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class TestDecoratorPatterns:
    """Test decorator patterns"""
    
    def test_function_decorator(self):
        """Test function decorator"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                wrapper.called = True
                return func(*args, **kwargs)
            wrapper.called = False
            return wrapper
        
        @decorator
        def test_func():
            return 42
        
        result = test_func()
        assert result == 42
        assert test_func.called
    
    def test_decorator_with_args(self):
        """Test decorator with arguments"""
        def repeat_decorator(times):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    results = []
                    for _ in range(times):
                        results.append(func(*args, **kwargs))
                    return results
                return wrapper
            return decorator
        
        @repeat_decorator(3)
        def test_func():
            return 42
        
        result = test_func()
        assert result == [42, 42, 42]
    
    def test_class_decorator(self):
        """Test class decorator"""
        def add_method(cls):
            cls.new_method = lambda self: 42
            return cls
        
        @add_method
        class TestClass:
            pass
        
        obj = TestClass()
        assert obj.new_method() == 42


class TestGeneratorPatterns:
    """Test generator patterns"""
    
    def test_simple_generator(self):
        """Test simple generator"""
        def gen():
            yield 1
            yield 2
            yield 3
        
        result = list(gen())
        assert result == [1, 2, 3]
    
    def test_generator_with_range(self):
        """Test generator with range"""
        def gen():
            for i in range(3):
                yield i * 2
        
        result = list(gen())
        assert result == [0, 2, 4]
    
    def test_generator_expression(self):
        """Test generator expression"""
        gen = (x * 2 for x in range(3))
        result = list(gen)
        assert result == [0, 2, 4]
    
    def test_generator_send(self):
        """Test generator send method"""
        def gen():
            value = yield
            yield value * 2
        
        g = gen()
        next(g)
        result = g.send(21)
        assert result == 42


class TestLambdaFunctions:
    """Test lambda function patterns"""
    
    def test_lambda_basic(self):
        """Test basic lambda"""
        square = lambda x: x ** 2
        assert square(5) == 25
    
    def test_lambda_with_map(self):
        """Test lambda with map"""
        numbers = [1, 2, 3, 4]
        result = list(map(lambda x: x * 2, numbers))
        assert result == [2, 4, 6, 8]
    
    def test_lambda_with_filter(self):
        """Test lambda with filter"""
        numbers = [1, 2, 3, 4, 5]
        result = list(filter(lambda x: x % 2 == 0, numbers))
        assert result == [2, 4]
    
    def test_lambda_with_sorted(self):
        """Test lambda with sorted"""
        items = [(2, 'b'), (1, 'a'), (3, 'c')]
        result = sorted(items, key=lambda x: x[1])
        assert result == [(1, 'a'), (2, 'b'), (3, 'c')]


class TestFunctionalProgramming:
    """Test functional programming patterns"""
    
    def test_reduce_sum(self):
        """Test reduce for sum"""
        numbers = [1, 2, 3, 4, 5]
        result = reduce(operator.add, numbers)
        assert result == 15
    
    def test_reduce_product(self):
        """Test reduce for product"""
        numbers = [1, 2, 3, 4, 5]
        result = reduce(operator.mul, numbers)
        assert result == 120
    
    def test_reduce_with_initializer(self):
        """Test reduce with initializer"""
        numbers = [1, 2, 3]
        result = reduce(operator.add, numbers, 100)
        assert result == 106
    
    def test_map_reduce_pattern(self):
        """Test map-reduce pattern"""
        data = [1, 2, 3, 4, 5]
        mapped = list(map(lambda x: x * 2, data))
        result = reduce(operator.add, mapped)
        assert result == 30


class TestContextAndState:
    """Test context and state management"""
    
    def test_state_machine(self):
        """Test state machine pattern"""
        class StateMachine:
            def __init__(self):
                self.state = 'START'
            
            def transition(self, event):
                if self.state == 'START' and event == 'RUN':
                    self.state = 'RUNNING'
                elif self.state == 'RUNNING' and event == 'STOP':
                    self.state = 'STOPPED'
        
        sm = StateMachine()
        assert sm.state == 'START'
        
        sm.transition('RUN')
        assert sm.state == 'RUNNING'
        
        sm.transition('STOP')
        assert sm.state == 'STOPPED'
    
    def test_property_pattern(self):
        """Test property pattern"""
        class Person:
            def __init__(self, name):
                self._name = name
            
            @property
            def name(self):
                return self._name
            
            @name.setter
            def name(self, value):
                self._name = value
        
        person = Person("Alice")
        assert person.name == "Alice"
        
        person.name = "Bob"
        assert person.name == "Bob"


class TestCollectionsPatterns:
    """Test collections patterns"""
    
    def test_defaultdict(self):
        """Test defaultdict"""
        dd = defaultdict(list)
        dd['key'].append(1)
        dd['key'].append(2)
        
        assert dd['key'] == [1, 2]
        assert isinstance(dd['new_key'], list)
    
    def test_counter(self):
        """Test Counter"""
        items = ['a', 'b', 'a', 'c', 'b', 'a']
        counter = Counter(items)
        
        assert counter['a'] == 3
        assert counter['b'] == 2
        assert counter['c'] == 1
    
    def test_counter_most_common(self):
        """Test Counter most_common"""
        items = ['a', 'b', 'a', 'c', 'b', 'a']
        counter = Counter(items)
        most_common = counter.most_common(1)
        
        assert most_common[0] == ('a', 3)


class TestDateTimeOperations:
    """Test datetime operations"""
    
    def test_datetime_creation(self):
        """Test datetime creation"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
    
    def test_datetime_arithmetic(self):
        """Test datetime arithmetic"""
        dt1 = datetime(2024, 1, 1)
        dt2 = datetime(2024, 1, 5)
        
        diff = dt2 - dt1
        assert diff.days == 4
    
    def test_datetime_formatting(self):
        """Test datetime formatting"""
        dt = datetime(2024, 1, 1, 12, 30, 45)
        formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert formatted == "2024-01-01 12:30:45"
    
    def test_timedelta_operations(self):
        """Test timedelta operations"""
        td = timedelta(days=1, hours=2, minutes=30)
        total_seconds = td.total_seconds()
        assert total_seconds == (1 * 24 * 3600 + 2 * 3600 + 30 * 60)


class TestErrorHandlingPatterns:
    """Test error handling patterns"""
    
    def test_try_except_else(self):
        """Test try-except-else"""
        result = None
        
        try:
            result = 10 / 2
        except ZeroDivisionError:
            result = -1
        else:
            result = result * 2
        
        assert result == 10
    
    def test_multiple_exception_handlers(self):
        """Test multiple exception handlers"""
        def handle_error(value):
            try:
                return 10 / value
            except ZeroDivisionError:
                return "Division by zero"
            except TypeError:
                return "Type error"
        
        assert handle_error(0) == "Division by zero"
        assert handle_error("string") == "Type error"
    
    def test_exception_chaining(self):
        """Test exception chaining"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise RuntimeError("New error") from e
        except RuntimeError as e:
            assert str(e) == "New error"
            assert isinstance(e.__cause__, ValueError)


class TestMetaclassPatterns:
    """Test metaclass patterns"""
    
    def test_singleton_metaclass(self):
        """Test singleton metaclass"""
        class SingletonMeta(type):
            _instances = {}
            
            def __call__(cls, *args, **kwargs):
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
                return cls._instances[cls]
        
        class Singleton(metaclass=SingletonMeta):
            pass
        
        obj1 = Singleton()
        obj2 = Singleton()
        
        assert obj1 is obj2
    
    def test_metaclass_modification(self):
        """Test metaclass modification"""
        class TrackerMeta(type):
            def __new__(mcs, name, bases, attrs):
                attrs['tracked'] = True
                return super().__new__(mcs, name, bases, attrs)
        
        class TrackedClass(metaclass=TrackerMeta):
            pass
        
        assert TrackedClass.tracked


class TestDuckTyping:
    """Test duck typing patterns"""
    
    def test_duck_typing_basic(self):
        """Test basic duck typing"""
        class Duck:
            def quack(self):
                return "Quack!"
        
        class Person:
            def quack(self):
                return "Quack like a duck!"
        
        def make_sound(obj):
            return obj.quack()
        
        duck = Duck()
        person = Person()
        
        assert make_sound(duck) == "Quack!"
        assert make_sound(person) == "Quack like a duck!"
    
    def test_protocol_pattern(self):
        """Test protocol pattern"""
        class Drawable:
            def draw(self):
                pass
        
        class Circle(Drawable):
            def draw(self):
                return "Drawing circle"
        
        class Square(Drawable):
            def draw(self):
                return "Drawing square"
        
        shapes = [Circle(), Square()]
        results = [shape.draw() for shape in shapes]
        
        assert results == ["Drawing circle", "Drawing square"]


class TestMROAndInheritance:
    """Test Method Resolution Order and inheritance"""
    
    def test_simple_inheritance(self):
        """Test simple inheritance"""
        class Parent:
            def method(self):
                return "parent"
        
        class Child(Parent):
            def method(self):
                return "child"
        
        child = Child()
        assert child.method() == "child"
    
    def test_multiple_inheritance(self):
        """Test multiple inheritance"""
        class Mixin1:
            def method1(self):
                return "mixin1"
        
        class Mixin2:
            def method2(self):
                return "mixin2"
        
        class Combined(Mixin1, Mixin2):
            pass
        
        obj = Combined()
        assert obj.method1() == "mixin1"
        assert obj.method2() == "mixin2"
    
    def test_super_call(self):
        """Test super() call"""
        class Parent:
            def method(self):
                return "parent"
        
        class Child(Parent):
            def method(self):
                return super().method() + "_child"
        
        child = Child()
        assert child.method() == "parent_child"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
