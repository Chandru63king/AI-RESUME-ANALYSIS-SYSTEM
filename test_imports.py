
try:
    print("Testing imports...")
    from flask import Flask, render_template, request, redirect, session, url_for, g, jsonify, Response
    print("Flask imported.")
    import sqlite3
    import os
    import re
    from werkzeug.utils import secure_filename
    print("Standard libs imported.")
    from ai_engine.resume_parser import ResumeParser
    print("ResumeParser imported.")
    from ai_engine.job_matcher import JobMatchEngine
    print("JobMatchEngine imported.")
    
    print("\nTesting ResumeParser instantiation (spaCy load)...")
    parser = ResumeParser()
    print("ResumeParser instantiated.")
    
    print("\nTesting JobMatchEngine instantiation...")
    matcher = JobMatchEngine()
    print("JobMatchEngine instantiated.")
    
    print("\nSUCCESS: All imports and instantiations passed.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
