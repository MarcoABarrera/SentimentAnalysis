from pyflink.datastream import StreamExecutionEnvironment
#this code was only used to test pyflink
def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # Print a simple message
    env.from_collection([1, 2, 3, 4, 5]) \
        .map(lambda x: x * x) \
        .print()

    env.execute("Test PyFlink")

if __name__ == '__main__':
    main()