"""B5 single-candidate entry point using the evaluated G3 prompt by default."""
import sys
import run_spec_card_ab


def main():
    original = sys.argv[:]
    try:
        if '--closed-loop' in original:
            import run_json_pipeline
            arguments = original[1:]
            arguments.remove('--closed-loop')
            arguments = ['--cases' if arg == '--case' else '--rtl-prompt' if arg == '--direct-prompt' else arg for arg in arguments]
            sys.argv = [original[0], '--rtl-prompt', 'g3', *arguments]
            return run_json_pipeline.main()
        # Defaults precede user arguments so explicit options remain effective.
        sys.argv = [original[0], "--arm", "direct", "--max-repairs", "0",
                    "--direct-prompt", "g3", *original[1:]]
        return run_spec_card_ab.main()
    finally:
        sys.argv = original


if __name__ == "__main__":
    raise SystemExit(main())
